import asyncio
import inspect
import logging
from collections.abc import Awaitable, Callable
from typing import Annotated, Any, cast, override

from bson import ObjectId
from nats.aio.client import Client as NATS
from nats.js import JetStreamContext
from redis.asyncio import Redis
from swiss_ai_hub.core.agents import AgentConfig, StepConfig
from swiss_ai_hub.core.dispatcher import BaseDispatcher, EventsAndKwargs, TraceStore
from swiss_ai_hub.core.displayers import EventDisplayer
from swiss_ai_hub.core.events import BaseEvent
from swiss_ai_hub.core.events.agent import AgentInTheLoopRequestEvent, ControlEvent, ExceptionEvent, StartEvent
from swiss_ai_hub.core.form.form import Form
from swiss_ai_hub.core.form.normalization import transform_formkit_arrays
from swiss_ai_hub.core.generative_ai import AgentMemory
from swiss_ai_hub.core.i18n import LocaleHandler
from swiss_ai_hub.core.rpc import AgentConfigClient
from swiss_ai_hub.core.subscribers import AgentNCSubscriber
from swiss_ai_hub.core.topic_managers import AgentClassTopicManager, AgentThreadTopicManager
from swiss_ai_hub.core.topics import AgentInstanceTopic, PartialAgentTopic, Topic
from swiss_ai_hub.core.topics.agents.agent_class_topic import AgentClassTopic

from swiss_ai_hub.agent.agents.agent import Agent
from swiss_ai_hub.agent.context.run.run_context import RunContext
from swiss_ai_hub.agent.context.thread.thread_context import ThreadContext
from swiss_ai_hub.agent.i18n.agent_locale_handler import AgentLocaleHandler
from swiss_ai_hub.agent.tracing.agent_run_tracer import AgentRunTracer

logger = logging.getLogger(__name__)


class AgentDispatcher(BaseDispatcher):
    """
    The AgentDispatcher builds on the BaseDispatcher and adds functionality that is only specific to agentic
    dispatchable workflows. These concepts are:

    1. **Context and State Management:**
        The AgentDispatcher uses `RunContext` and `ThreadContext` for state persistence.
        It interacts with `DistributedEventStore` and `StepStore` to track event
        histories and step execution counts across distributed environments.

    2. **Tracing and Telemetry:**
        Through `AgentRunTracer`, it logs start/end times of runs and steps, aiding observability.

    3. **Configuration Fetching via RPC:**
        When processing StartEvents, the dispatcher fetches the agent configuration from the API
        via NATS request-reply using the agent_id from the event. This decouples configuration
        management from event payloads.

        The fetched config is merged with non-configurable values (deployment-specific settings)
        from the local agent_config to produce the final runtime configuration.
    """

    _AGENT_CONFIG_KEY = "_agent_config"
    _AIHUB_HEADERS_KEY = "aihub_headers"

    def __init__(
        self,
        agent: Annotated[type[Agent], "The agent class defining steps and logic."],
        agent_config: Annotated[
            AgentConfig, "Form-mode configuration with FormKit elements and non-configurable values."
        ],
        nc: Annotated[NATS, "NATS client for messaging."],
        js: Annotated[
            JetStreamContext,
            "JetStream context for persistent storage and event streams.",
        ],
        redis: Annotated[Redis, "Redis client for distributed storage."],
        topic_manager: Annotated[AgentClassTopicManager, "Manages event subjects for this agent instance."],
        locale_handler: Annotated[AgentLocaleHandler, "Manages localization for the agent."],
    ):
        super().__init__(nc, js, redis, topic_manager, AgentClassTopic, dispatch_entity_name=agent.__name__)
        self.agent = agent
        self.agent_config = agent_config
        self.locale_handler = locale_handler

        self.agent_config_type: type[AgentConfig] = self.agent_config.__class__

        # Pre-compute non-configurable values for merging with incoming configs
        self._non_configurable_values = agent_config.get_non_configurable_values()

        self.trace_store = TraceStore(redis)
        self.agent_run_tracer = AgentRunTracer(self.trace_store)

        # Client for fetching agent configuration via NATS RPC
        self._config_client = AgentConfigClient(nc=nc)

    @override
    async def handle_event(
        self,
        event: Annotated[ControlEvent, "The incoming control event to handle."],
        topic: Annotated[AgentClassTopic, "The parsed topic of the event."],
    ):
        """
        Called whenever a new event arrives. This method:
        - Stores the event.
        - Manages the run's open-telemetry trace.
        - Handles run lifecycle changes (Start, Stop, Exception).
        - Checks for and triggers ready steps asynchronously.
        """
        await super().handle_event(event, topic)

        # Retrieve contexts (run and thread)
        run_context = RunContext.for_topic(self.redis, topic)
        thread_context = ThreadContext.for_topic(self.redis, topic)
        agent_config_dict: dict[str, Any] | None = None

        # Propagate X-AIHub-* request headers into RunContext so downstream steps can act on behalf
        # of the user. Written on every header-carrying event, not only StartEvent, so HITL/BITL
        # responses refresh the stored token instead of reusing a stale one.
        if event._aihub_headers:
            await run_context.set(self._AIHUB_HEADERS_KEY, event._aihub_headers)

        if event.is_start_event:
            event = cast(StartEvent, event)

            submitted_config = await self._config_client.fetch_config(
                agent_class=self.agent.__name__,
                agent_id=topic.agent_id,
            )

            # Deep merge: non-configurable values (from form-mode config) + configurable values (from submission)
            agent_config_dict = Form.deep_merge(self._non_configurable_values, submitted_config)

            await run_context.set(self._AGENT_CONFIG_KEY, agent_config_dict)

        if agent_config_dict is None:
            agent_config_dict = await run_context.get(self._AGENT_CONFIG_KEY)
            if agent_config_dict is None:
                raise ValueError(f"No agent config found for event {event.event_name} and topic {topic}")

        # Transform FormKit-style arrays (dict with numeric keys) to Python lists
        agent_config_dict = transform_formkit_arrays(agent_config_dict)
        run_agent_config = self.agent_config_type.model_validate(agent_config_dict)
        topic = AgentInstanceTopic.from_agent_class_topic(
            agent_class_topic=topic,
            agent_id=run_agent_config.agent_id,
        )

        if event.is_start_event:
            event = cast(StartEvent, event)
            logger.debug(f"Handling StartEvent: {event.event_name}")

            await self.agent_run_tracer.trace_run_start(topic=topic, event=event)

            # Store any initial data from the StartEvent into run_context
            event_data = event.to_context_dict()
            for key, value in event_data.items():
                logger.debug(f"Setting key '{key}' in run_context")
                await run_context.set(key, value)

        if event.is_stop_event or event.is_exception_event:
            logger.debug(f"Handling final event: {event.event_name}")

            await run_context.delete_all()
            await self.event_store.delete_all(topic.execution_context_id)
            await self.step_store.delete_all(topic.execution_context_id)
            await self.trace_store.delete_all(topic.execution_context_id)

            if event.is_exception_event:
                await self.step_store.mark_execution_context_as_crashed(topic.execution_context_id)
            return

        steps = self.agent.get_steps_waiting_for_event(type(event))
        for step_method in steps:
            logger.debug(f"Checking step '{step_method.__name__}' for readiness")
            input_events = getattr(step_method, Agent.INPUT_EVENTS_ANNOTATION, set())
            input_event_class_names = [event_class.event_name_from_class() for event_class in input_events]
            events = await self.event_store.get_events_of_multiple_types(
                topic.execution_context_id, input_event_class_names, until_event=event
            )
            if await self.is_step_ready(
                event, step_method, events, run_context, thread_context, topic, run_agent_config
            ):
                logger.debug(f"Triggering step '{step_method.__name__}' due to event '{event.event_name}'")
                task = asyncio.create_task(
                    self.execute_step(event, step_method, events, run_context, thread_context, topic, run_agent_config)
                )
                self._background_tasks.add(task)
                task.add_done_callback(self._background_tasks.discard)

    @override
    async def is_step_ready(
        self,
        trigger_event: Annotated[ControlEvent, "The event that caused this step to trigger."],
        step_method: Annotated[Callable, "The step method to check."],
        events: Annotated[dict[str, list[ControlEvent]], "All events for this run, keyed by event name."],
        run_context: Annotated[RunContext, "Per-run context for state and configuration."],
        thread_context: Annotated[ThreadContext, "Per-thread context for longer-lived state."],
        topic: Annotated[AgentInstanceTopic, "Topic info for the current run and thread."],
        agent_config: Annotated[AgentConfig, "The agent configuration for this run."],
    ) -> bool:
        """
        Checks if a step can be run given the current state (events available, max executions, etc.).

        It verifies:
        - The run hasn't crashed.
        - All required input events are available in the needed quantities.

        Returns True if the step can execute, False otherwise.
        """
        # Must be first thing to be checked, as it ensures execution has not crashed
        if not await self._step_meets_basic_execution_requirements(step_method, events, topic):
            return False

        max_executions = getattr(step_method, Agent.MAX_EXECUTION_PER_RUN_ANNOTATION, None)
        if max_executions is not None:
            execution_count = await self.step_store.get_execution_count(
                topic.execution_context_id, step_method.__name__
            )
            if execution_count >= max_executions:
                logger.debug(
                    f"[{step_method.__name__}] Max executions reached ({execution_count}/{max_executions}), skipping."
                )
                return False

        precondition_fn: Callable[..., Awaitable[bool]] | None = getattr(
            step_method, Agent.PRECONDITION_FUNCTION_ANNOTATION, None
        )

        if precondition_fn:
            precondition_events_and_kwargs = await self._build_method_kwargs(
                trigger_event, precondition_fn, events, run_context, thread_context, topic, agent_config
            )
            is_ready = await precondition_fn(**precondition_events_and_kwargs.kwargs)
            if not is_ready:
                logger.debug(f"[{step_method.__name__}] Ready function returned False, skipping.")
                return False

        logger.debug(f"[{step_method.__name__}] All specific input requirements satisfied.")
        return True

    @override
    async def execute_step(
        self,
        trigger_event: Annotated[ControlEvent, "The event that caused this step to trigger."],
        step_method: Annotated[Callable, "The step method to execute."],
        events: Annotated[dict[str, list[ControlEvent]], "All events for this run, keyed by event name."],
        run_context: Annotated[RunContext, "Per-run context for state and configuration."],
        thread_context: Annotated[ThreadContext, "Per-thread context for longer-lived state."],
        topic: Annotated[AgentInstanceTopic, "Topic info for the current run and thread."],
        agent_config: Annotated[AgentConfig, "The agent configuration for this run."],
    ):
        """
        Executes a step method:
        1. Increments step execution count to avoid race conditions in distributed environments.
        2. Constructs kwargs by retrieving appropriate events and other dependencies.
        3. Calls the step method on a new agent instance.
        4. Publishes any output events from the step.

        On errors:
        - Logs the exception.
        - Publishes an ExceptionEvent if `_stop_on_error` is True.
        """
        max_executions = getattr(step_method, Agent.MAX_EXECUTION_PER_RUN_ANNOTATION, None)

        if max_executions is not None:
            await self.step_store.increment_execution_count(topic.execution_context_id, step_method.__name__)

        events_and_kwargs: EventsAndKwargs = await self._build_method_kwargs(
            trigger_event,
            step_method,
            events,
            run_context,
            thread_context,
            topic,
            agent_config,
        )

        # Ensure step is not executed twice with the exact same input events
        duplicated_run = await self.step_store.was_called_with_events(
            topic.execution_context_id, step_method.__name__, events_and_kwargs.events
        )
        if duplicated_run:
            logger.debug(f"Skipping step '{step_method.__name__}' as it has already been called with the same events.")
            return

        await self.step_store.report_execution_context_with_events(
            topic.execution_context_id, step_method.__name__, events_and_kwargs.events
        )

        # Instantiate the agent and run the step
        agent_instance = self.agent()

        async with self.agent_run_tracer.trace_step_start(topic, step_method, events_and_kwargs.kwargs) as step_span:
            try:
                result = await step_method(agent_instance, **events_and_kwargs.kwargs)
            except Exception as e:
                self.agent_run_tracer.trace_step_error(step_span, e)
                if getattr(step_method, Agent.STOP_ON_ERROR_ANNOTATION, False):
                    event = ExceptionEvent(message=str(e))
                    await self.publish_event(event, topic)
                logger.exception(e)
                logger.exception(f"Error executing step '{step_method.__name__}': {e}")
                return

            # Always finalize the span so Langfuse receives trace metadata (name, session,
            # user) even for steps that return None (e.g. side-effect-only steps).
            result_events = None
            if result:
                if not isinstance(result, list):
                    result = [result]
                result_events = result

            await self.agent_run_tracer.trace_step_stop(step_span, result_events, topic)

            # If the step returns events, publish them
            if result_events:
                for event in result_events:
                    if event.is_hitl_request_event:
                        logger.debug(f"Handling special event: HumanInTheLoopRequestEvent: {event.event_name}")
                        # Complete the event's topic info
                        event.topic = AgentInstanceTopic.from_partial_topic(
                            partial_topic=event.topic,
                            agent_class=topic.agent_class,
                            agent_id=topic.agent_id,
                            run_id=topic.run_id,
                            thread_id=topic.thread_id,
                            display_id=topic.display_id,
                            event_id=event.event_id,
                        )

                    if event.is_bitl_request_event:
                        logger.debug(f"Handling special event: BotInTheLoopRequestEvent: {event.event_name}")
                        # Complete the event's topic info
                        event.topic = AgentInstanceTopic.from_partial_topic(
                            partial_topic=event.topic,
                            agent_class=topic.agent_class,
                            agent_id=topic.agent_id,
                            run_id=topic.run_id,
                            thread_id=topic.thread_id,
                            display_id=topic.display_id,
                            event_id=event.event_id,
                        )

                    if event.is_aitl_request_event:
                        logger.debug(f"Handling special event: AgentInTheLoopRequestEvent: {event.event_name}")
                        await self.trigger_agent_in_the_loop(event, topic)

                    await self.publish_event(event, topic)

    @override
    async def publish_event(
        self,
        event: Annotated[BaseEvent, "The event to publish."],
        topic: Annotated[AgentInstanceTopic, "Current run/thread topic context."],
    ):
        """
        Publishes a given event (Control or Display) to the correct subject.
        Uses the per-thread topic manager to form the right event subject and publishes via JSPublisher.
        """
        topic_manager = self.get_topic_manager_for_thread(topic)
        if event.is_control_event:
            subject = topic_manager.get_subject_for_control_event_in_thread(event.event_name, event.event_id)
            await self.js_publisher.publish_event(event, subject)
        if event.is_display_event:
            subject = topic_manager.get_subject_for_display_event_in_thread(event.event_name, event.event_id)
            await self.nc_publisher.publish_event(event, subject)

    async def _build_method_kwargs(
        self,
        trigger_event: Annotated[ControlEvent, "The event that caused this step to trigger."],
        method: Annotated[Callable, "The method to prepare the args for."],
        events: Annotated[dict[str, list[ControlEvent]], "All events for this run, keyed by event name."],
        run_context: Annotated[RunContext, "Per-run context for state and configuration."],
        thread_context: Annotated[ThreadContext, "Per-thread context for longer-lived state."],
        topic: Annotated[AgentInstanceTopic, "Topic info for the current run and thread."],
        agent_config: Annotated[AgentConfig, "The agent configuration for this run."],
    ) -> EventsAndKwargs:
        step_signature = inspect.signature(method)
        events_and_kwargs: EventsAndKwargs = await self._build_event_kwargs(trigger_event, method, events)
        step_configs: dict[type[StepConfig], StepConfig] = agent_config.get_step_configs()

        for param in step_signature.parameters.values():
            param_value = await self._get_parameter_value(
                param, step_configs, agent_config, run_context, thread_context, topic
            )
            if param_value is not None:
                events_and_kwargs.kwargs[param.name] = param_value

        return events_and_kwargs

    async def _get_parameter_value(
        self,
        param: Annotated[inspect.Parameter, "Parameter from the step method signature."],
        step_configs: Annotated[dict[type[StepConfig], StepConfig], "Step configurations for the agent."],
        agent_config: Annotated[AgentConfig, "The agent configuration for this run."],
        run_context: Annotated[RunContext, "Per-run context for state and configuration."],
        thread_context: Annotated[ThreadContext, "Per-thread context for longer-lived state."],
        topic: Annotated[AgentInstanceTopic, "Topic info for the current run and thread."],
    ) -> Annotated[Any, "The value to inject for the parameter."]:
        if step_configs.get(param.annotation):
            return step_configs[param.annotation]

        if inspect.isclass(param.annotation) and issubclass(param.annotation, AgentConfig):
            if param.annotation != self.agent_config_type:
                raise ValueError(
                    f"Expected AgentConfig type '{self.agent_config_type.__name__}', "
                    f"but got '{param.annotation.__name__}' for parameter '{param.name}'."
                )
            logger.debug(
                f"Injected dynamic configuration for parameter '{param.name}' of type '{param.annotation.__name__}'"
            )
            return agent_config

        if param.annotation == RunContext:
            return run_context

        if param.annotation == ThreadContext:
            return thread_context

        if param.annotation == EventDisplayer:
            return EventDisplayer(
                self.js_publisher,
                topic_manager=self.get_topic_manager_for_thread(topic),
            )

        if param.annotation in [LocaleHandler, AgentLocaleHandler]:
            locale = await run_context.get("locale", LocaleHandler.DEFAULT_LOCALE)
            return self.locale_handler.in_locale(locale)

        if param.annotation == AgentMemory:
            locale = await run_context.get("locale", LocaleHandler.DEFAULT_LOCALE)
            return AgentMemory(
                agent_config=agent_config, agent_class=self.agent.__name__, t=self.locale_handler.in_locale(locale)
            )

        if param.annotation in [AgentInstanceTopic, AgentClassTopic, PartialAgentTopic]:
            return topic

        return None

    def get_topic_manager_for_thread(
        self, topic: Annotated[AgentInstanceTopic, "Topic identifying the run/thread."]
    ) -> AgentThreadTopicManager:
        """
        Returns a thread-specific topic manager derived from the agent's instance topic manager.
        Useful for publishing thread-scoped events.
        """
        return AgentThreadTopicManager.from_agent_class_topic_manager(
            topic_manager=self.topic_manager,
            agent_id=topic.agent_id,
            thread_id=topic.thread_id,
            display_id=topic.display_id,
            run_id=topic.run_id,
        )

    async def trigger_agent_in_the_loop(
        self, aitl_request_event: AgentInTheLoopRequestEvent, topic: AgentInstanceTopic
    ):
        """
        Orchestrates agent-to-agent delegation by creating a temporary subscription to the delegated agent.
        When agents collaborate, we need a way to route responses back to the requesting agent.
        A temporary subscription:
        - Ensures responses are captured even in distributed environments
        - Allows proper cleanup after the interaction completes
        - Maintains isolation between different agent-to-agent interactions
        - Enables monitoring of both successful completions and failures
        """
        response_event_class = aitl_request_event.response
        exception_event_class = aitl_request_event.exception

        start_event = aitl_request_event.start_event

        aitl_run_id = topic.run_id if aitl_request_event.share_run_id else str(ObjectId())
        aitl_thread_id = topic.thread_id if aitl_request_event.share_thread_id else str(ObjectId())
        aitl_display_id = topic.display_id if aitl_request_event.share_display_id else str(ObjectId())

        aitl_request_event.other_agent_topic = AgentInstanceTopic.from_partial_topic(
            partial_topic=aitl_request_event.other_agent_topic,
            thread_id=aitl_thread_id,
            display_id=aitl_display_id,
            run_id=aitl_run_id,
        )

        aitl_wrapper_span = await self.agent_run_tracer.start_aitl_wrapper_span(
            caller_topic=topic,
            target_agent_class=aitl_request_event.other_agent_topic.agent_class,
            target_agent_id=aitl_request_event.other_agent_topic.agent_id,
            target_run_id=aitl_run_id,
            target_thread_id=aitl_thread_id,
            start_event=start_event,
        )

        target_topic = aitl_request_event.other_agent_topic

        async def convert_event_to_agent_in_the_loop_response(aitl_event: BaseEvent, aitl_topic: Topic):
            if aitl_event.is_stop_event:
                aitl_response = response_event_class(stop_event=aitl_event)
                logger.debug(f"Received Agent in the Loop StopEvent: {aitl_response}, stopping subscriber.")
                await event_subscriber.stop()
                await self.agent_run_tracer.end_aitl_wrapper_span(
                    aitl_wrapper_span, success=True, target_topic=target_topic
                )
                await self.publish_event(aitl_response, topic)
            if aitl_event.is_exception_event:
                aitl_exception = exception_event_class(exception_event=aitl_event)
                logger.debug(f"Received Agent in the Loop ExceptionEvent: {aitl_exception}, stopping subscriber.")
                await event_subscriber.stop()
                await self.agent_run_tracer.end_aitl_wrapper_span(
                    aitl_wrapper_span, success=False, target_topic=target_topic
                )
                await self.publish_event(aitl_exception, topic)

        logger.debug(f"Temporarily subscribing to {aitl_request_event.other_agent_topic}")
        event_subscriber = AgentNCSubscriber.for_thread_control_events(
            nc=self.nc,
            topic_manager=AgentThreadTopicManager.from_agent_topic(aitl_request_event.other_agent_topic),
            handler=convert_event_to_agent_in_the_loop_response,
            subscriber_name=f"{self.agent.__name__}DispatcherAgentInTheLoop",
        )
        await event_subscriber.start()

        subject = aitl_request_event.other_agent_topic.to_subject()
        logger.debug(f"Publishing to Agent in the Loop to subject {subject}")
        await self.js_publisher.publish_event(start_event, subject)
