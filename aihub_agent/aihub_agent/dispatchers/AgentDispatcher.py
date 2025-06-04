import asyncio
import inspect
import logging
from typing import Annotated, Any, Awaitable, Callable, Dict, List, Optional, Tuple, Type

from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.displayers.EventDisplayer import EventDisplayer
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.nats.context.run.RunContext import RunContext
from aihub_lib.nats.context.thread.ThreadContext import ThreadContext
from aihub_lib.nats.dispatcher.BaseDispatcher import BaseDispatcher
from aihub_lib.nats.events import BaseEvent, ControlEvent, ExceptionEvent
from aihub_lib.nats.events.agent_in_the_loop.request.AgentInTheLoopRequestEvent import AgentInTheLoopRequestEvent
from aihub_lib.nats.subscribers.NCSubscriber import NCSubscriber
from aihub_lib.nats.topic_managers.agents.AgentInstanceTopicManager import AgentInstanceTopicManager
from aihub_lib.nats.topic_managers.agents.AgentThreadTopicManager import AgentThreadTopicManager
from aihub_lib.nats.topics import Topic
from aihub_lib.nats.topics.agents.AgentTopic import AgentTopic
from bson import ObjectId
from cachetools import TTLCache
from nats.aio.client import Client as NATS
from nats.js import JetStreamContext
from redis.asyncio import Redis

from aihub_agent.agents.Agent import Agent
from aihub_agent.i18n.AgentLocaleHandler import AgentLocaleHandler
from aihub_agent.tracing.coordinators.RunTraceCoordinator import RunTraceCoordinator

logger = logging.getLogger(__name__)


class AgentDispatcher(BaseDispatcher):
    """
    The AgentDispatcher orchestrates the execution of workflow steps within an agent run. It acts as the
    central coordinator that listens to events, determines which steps should fire, injects the right
    parameters into those steps, and handles the lifecycle of runs (start, error, stop).

    ### Why the AgentDispatcher?
    A workflow often involves multiple steps that depend on certain events. The AgentDispatcher ties all these
    concepts together:
    - It receives events (like `StartEvent`, `StopEvent`, custom `ControlEvent`s).
    - Finds which steps are "ready" to execute based on available events and step definitions.
    - Fetches needed contextual data (thread/run contexts, previous events) and constructs the arguments
      for the steps.
    - Executes steps and publishes any resulting events, updating the run’s state as needed.

    By centralizing these responsibilities, the AgentDispatcher ensures consistent, reliable orchestration of
    complex multi-step workflows.

    ### Key Responsibilities
    1. **Event Handling:**
       `handle_event` is called for each new event. It:
       - Stores the event.
       - Updates run/thread context as required.
       - Determines which steps (if any) become executable due to the new event.
       - Executes those steps asynchronously.

    2. **Step Execution Logic:**
       Steps might have constraints:
       - Input events that must be present in certain quantities.
       - Optional parameters.
       - Maximum number of executions per run.
       The AgentDispatcher enforces these rules in `is_step_ready` and `execute_step`.

    3. **Context and State Management:**
       The AgentDispatcher uses `RunContext` and `ThreadContext` for state persistence. It interacts with `DistributedEventStore`
       and `StepStore` to track event histories and step execution counts across distributed environments.

    4. **Tracing and Telemetry:**
       Through `RunTraceCoordinator`, it logs start/end times of runs and steps, aiding observability.

    ### Lifecycle
    A typical flow might be:
    - On a `StartEvent`, the run is initialized, contexts are set, tracing begins.
    - Incoming events trigger checks for steps that can run.
    - Steps run and produce new events, potentially enabling further steps.
    - On completion (`StopEvent`), the AgentDispatcher cleans up run-level data.

    ### Integration with Other Components
    - **Agent & Steps:** The AgentDispatcher uses the agent’s defined steps and their annotated metadata (like required events).
    - **Publishers & Stores:** It uses JSPublisher to publish resulting events, and distributed stores to fetch/update events or steps info.
    - **Tracing & Localization:** Integrates with `RunTraceCoordinator` for metrics and `AgentLocaleHandler` for localized outputs.
    """

    _telemetry_header_cache = TTLCache(maxsize=10_000, ttl=300)

    def __init__(
        self,
        agent: Annotated[Type[Agent], "The agent class defining steps and logic."],
        agent_config: Annotated[AgentConfig, "Configuration object for the agent, including step configs."],
        nc: Annotated[NATS, "NATS client for messaging."],
        js: Annotated[
            JetStreamContext,
            "JetStream context for persistent storage and event streams.",
        ],
        redis: Annotated[Redis, "Redis client for distributed storage."],
        topic_manager: Annotated[AgentInstanceTopicManager, "Manages event subjects for this agent instance."],
        locale_handler: Annotated[AgentLocaleHandler, "Manages localization for the agent."],
    ):
        super().__init__(nc, js, redis, topic_manager, AgentTopic)
        self.agent = agent
        self.agent_config = agent_config
        self.locale_handler = locale_handler

        self.tracer = RunTraceCoordinator(
            self.nc, project_name=locale_handler.extract_multi_locale(agent_config.name, "en")
        )
        self.step_configs = agent_config.get_step_configs()

    async def handle_event(
        self,
        event: Annotated[ControlEvent, "The incoming control event to handle."],
        topic: Annotated[AgentTopic, "The parsed topic of the event."],
    ):
        """
        Called whenever a new event arrives. This method:
        - Stores the event.
        - Updates run/thread contexts if necessary.
        - If the event is Start/Stop/Exception, handles run lifecycle changes.
        - Checks for steps that can now execute due to the event.

        If steps are ready, it triggers their execution asynchronously.
        """
        await super().handle_event(event, topic)

        # Retrieve contexts (run and thread)
        run_context = RunContext(self.redis, topic.thread_id, topic.run_id)
        thread_context = ThreadContext(self.redis, topic.thread_id)

        if event.is_start_event:
            logger.debug(f"Handling StartEvent: {event.event_name}")
            telemetry_headers = self.tracer.trace_run_start(topic, event)
            await run_context.set("telemetry_headers", telemetry_headers)

            # Store any initial data from the StartEvent into run_context
            event_data = event.to_context_dict()
            for key, value in event_data.items():
                logger.debug(f"Setting key '{key}' in run_context to '{value}'")
                await run_context.set(key, value)

        if event.is_stop_event:
            logger.debug(f"Handling StopEvent: {event.event_name}")
            # Clean up run-specific data
            await run_context.delete_all()
            await self.event_store.delete_all(topic.execution_context_id)
            await self.step_store.delete_all(topic.execution_context_id)
            return

        if event.is_exception_event:
            logger.debug(f"Handling ExceptionEvent: {event.event_name}")
            # Mark run as crashed so no further steps are executed
            await self.step_store.mark_execution_context_as_crashed(topic.execution_context_id)
            return

        # Determine which steps need to be executed due to this event
        steps = self.agent.get_steps_waiting_for_event(type(event))
        for step_method in steps:
            logger.debug(f"Checking step '{step_method.__name__}' for readiness")
            input_events = getattr(step_method, "_input_events", set())
            input_event_class_names = [event_class.event_name_from_class() for event_class in input_events]
            events = await self.event_store.get_events_of_multiple_types(
                topic.execution_context_id, input_event_class_names, until_event=event
            )
            if await self.is_step_ready(event, step_method, events, run_context, thread_context, topic):
                logger.debug(f"Triggering step '{step_method.__name__}' due to event '{event.event_name}'")
                asyncio.create_task(self.execute_step(event, step_method, events, run_context, thread_context, topic))

    async def is_step_ready(
        self,
        trigger_event: Annotated[ControlEvent, "The event that caused this step to trigger."],
        step_method: Annotated[Callable, "The step method to check."],
        events: Annotated[Dict[str, List[ControlEvent]], "All events for this run, keyed by event name."],
        run_context: Annotated[RunContext, "Per-run context for state and configuration."],
        thread_context: Annotated[ThreadContext, "Per-thread context for longer-lived state."],
        topic: Annotated[AgentTopic, "Topic info for the current run and thread."],
    ) -> bool:
        """
        Checks if a step can be run given the current state (events available, max executions, etc.).

        It verifies:
        - The run hasn't crashed.
        - The step hasn't exceeded its max execution count.
        - All required input events are available in the needed quantities.

        Returns True if the step can execute, False otherwise.
        """
        if not self.step_meets_basic_execution_requirements(step_method, events, topic):
            return False

        precondition_fn: Optional[Callable[..., Awaitable[bool]]] = getattr(step_method, "_precondition_fn", None)

        if precondition_fn:
            _, precondition_args = await self._build_method_kwargs(
                trigger_event, precondition_fn, events, run_context, thread_context, topic
            )
            is_ready = await precondition_fn(**precondition_args)
            if not is_ready:
                logger.debug(f"[{step_method.__name__}] Ready function returned False, skipping.")
                return False

        logger.debug(f"[{step_method.__name__}] All specific input requirements satisfied.")
        return True

    async def execute_step(
        self,
        trigger_event: Annotated[ControlEvent, "The event that caused this step to trigger."],
        step_method: Annotated[Callable, "The step method to execute."],
        events: Annotated[Dict[str, List[ControlEvent]], "All events for this run, keyed by event name."],
        run_context: Annotated[RunContext, "Per-run context for state and configuration."],
        thread_context: Annotated[ThreadContext, "Per-thread context for longer-lived state."],
        topic: Annotated[AgentTopic, "Topic info for the current run and thread."],
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
        max_executions = getattr(step_method, "_max_executions_per_run", None)

        if max_executions is not None:
            await self.step_store.increment_execution_count(topic.execution_context_id, step_method.__name__)

        all_input_events, kwargs = await self._build_method_kwargs(
            trigger_event,
            step_method,
            events,
            run_context,
            thread_context,
            topic,
        )

        # Ensure step is not executed twice with the exact same input events
        duplicated_run = await self.step_store.was_called_with_events(
            topic.execution_context_id, step_method.__name__, all_input_events
        )
        if duplicated_run:
            logger.debug(f"Skipping step '{step_method.__name__}' as it has already been called with the same events.")
            return

        await self.step_store.report_execution_context_with_events(
            topic.execution_context_id, step_method.__name__, all_input_events
        )

        # Instantiate the agent and run the step
        agent_instance = self.agent()
        if topic.run_id not in self._telemetry_header_cache:
            telemetry_headers = await run_context.get("telemetry_headers")
            self._telemetry_header_cache[topic.run_id] = telemetry_headers
        else:
            telemetry_headers = self._telemetry_header_cache[topic.run_id]

        async with self.tracer.trace_step_start(telemetry_headers, topic, step_method, kwargs) as step_span:
            try:
                result = await step_method(agent_instance, **kwargs)
            except Exception as e:
                await self.tracer.trace_step_error(step_span, e)
                if getattr(step_method, "_stop_on_error", False):
                    event = ExceptionEvent(message=str(e))
                    await self.publish_event(event, topic)
                logger.exception(e)
                logger.exception(f"Error executing step '{step_method.__name__}': {e}")
                return

            # If the step returns events, publish them
            if result:
                if not isinstance(result, list):
                    result = [result]

                await self.tracer.trace_step_stop(step_span, result)

                for event in result:
                    if event.is_hitl_request_event:
                        logger.debug(f"Handling special event: HumanInTheLoopRequestEvent: {event}")
                        # Complete the event's topic info
                        event.topic = AgentTopic.from_partial_topic(
                            partial_topic=event.topic,
                            agent_class=topic.agent_class,
                            agent_id=topic.agent_id,
                            run_id=topic.run_id,
                            thread_id=topic.thread_id,
                            display_id=topic.display_id,
                            event_id=event.event_id,
                        )

                    if event.is_bitl_request_event:
                        logger.debug(f"Handling special event: BotInTheLoopRequestEvent: {event}")
                        # Complete the event's topic info
                        event.topic = AgentTopic.from_partial_topic(
                            partial_topic=event.topic,
                            agent_class=topic.agent_class,
                            agent_id=topic.agent_id,
                            run_id=topic.run_id,
                            thread_id=topic.thread_id,
                            display_id=topic.display_id,
                            event_id=event.event_id,
                        )

                    if event.is_aitl_request_event:
                        logger.debug(f"Handling special event: AgentInTheLoopRequestEvent: {event}")
                        await self.trigger_agent_in_the_loop(event, topic)

                    await self.publish_event(event, topic)

    async def _build_method_kwargs(
        self,
        trigger_event: Annotated[ControlEvent, "The event that caused this step to trigger."],
        method: Annotated[Callable, "The method to prepare the args for."],
        events: Annotated[Dict[str, List[ControlEvent]], "All events for this run, keyed by event name."],
        run_context: Annotated[RunContext, "Per-run context for state and configuration."],
        thread_context: Annotated[ThreadContext, "Per-thread context for longer-lived state."],
        topic: Annotated[AgentTopic, "Topic info for the current run and thread."],
    ) -> Tuple[List[ControlEvent], Dict[str, Any]]:
        step_signature = inspect.signature(method)
        all_input_events, kwargs = await self._build_event_kwargs(trigger_event, method, events)

        # Prepare arguments
        for param in step_signature.parameters.values():
            # Handle special configurations injected by agent_config.get_step_configs()
            if self.step_configs.get(param.annotation):
                kwargs[param.name] = self.step_configs[param.annotation]
                continue

            # Handle AgentConfig if requested
            if inspect.isclass(param.annotation) and issubclass(param.annotation, AgentConfig):
                kwargs[param.name] = self.agent_config
                continue

            # Handle RunContext / ThreadContext
            if param.annotation == RunContext:
                kwargs[param.name] = run_context
                continue
            if param.annotation == ThreadContext:
                kwargs[param.name] = thread_context
                continue

            # Handle EventDisplayer
            if param.annotation == EventDisplayer:
                kwargs[param.name] = EventDisplayer(
                    self.js_publisher,
                    topic_manager=self.get_topic_manager_for_thread(topic),
                )
                continue

            # Handle LocaleHandler
            if param.annotation in [LocaleHandler, AgentLocaleHandler]:
                locale = await run_context.get("locale", LocaleHandler.DEFAULT_LOCALE)
                kwargs[param.name] = self.locale_handler.in_locale(locale)

        return all_input_events, kwargs

    def get_topic_manager_for_thread(
        self, topic: Annotated[AgentTopic, "Topic identifying the run/thread."]
    ) -> AgentThreadTopicManager:
        """
        Returns a thread-specific topic manager derived from the agent's instance topic manager.
        Useful for publishing thread-scoped events.
        """
        return AgentThreadTopicManager.from_agent_instance_topic_manager(
            topic_manager=self.topic_manager,
            thread_id=topic.thread_id,
            display_id=topic.display_id,
            run_id=topic.run_id,
        )

    async def trigger_agent_in_the_loop(self, aitl_request_event: AgentInTheLoopRequestEvent, topic: AgentTopic):
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

        async def convert_event_to_agent_in_the_loop_response(aitl_event: BaseEvent, aitl_topic: Topic):
            if aitl_event.is_stop_event:
                aitl_response = response_event_class(stop_event=aitl_event)
                logger.debug(f"Received Agent in the Loop StopEvent: {aitl_response}, stopping subscriber.")
                await event_subscriber.stop()
                await self.publish_event(aitl_response, topic)
            if aitl_event.is_exception_event:
                aitl_exception = exception_event_class(exception_event=aitl_event)
                logger.debug(f"Received Agent in the Loop ExceptionEvent: {aitl_exception}, stopping subscriber.")
                await event_subscriber.stop()
                await self.publish_event(aitl_exception, topic)

        aitl_run_id = topic.run_id if aitl_request_event.share_run_id else str(ObjectId())
        aitl_thread_id = topic.thread_id if aitl_request_event.share_thread_id else str(ObjectId())
        aitl_display_id = topic.display_id if aitl_request_event.share_display_id else str(ObjectId())

        aitl_request_event.other_agent_topic = AgentTopic.from_partial_topic(
            partial_topic=aitl_request_event.other_agent_topic,
            thread_id=aitl_thread_id,
            display_id=aitl_display_id,
            run_id=aitl_run_id,
        )

        logger.debug(f"Temporarily subscribing to {aitl_request_event.other_agent_topic}")
        event_subscriber = NCSubscriber.for_all_thread_events(
            nc=self.nc,
            topic_manager=AgentThreadTopicManager.from_agent_topic(aitl_request_event.other_agent_topic),
            handler=convert_event_to_agent_in_the_loop_response,
        )
        await event_subscriber.start()

        subject = aitl_request_event.other_agent_topic.to_subject()
        logger.debug(f"Publishing to Agent in the Loop to subject {subject}")
        await self.js_publisher.publish_event(start_event, subject)

    async def publish_event(
        self,
        event: Annotated[BaseEvent, "The event to publish."],
        topic: Annotated[AgentTopic, "Current run/thread topic context."],
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
