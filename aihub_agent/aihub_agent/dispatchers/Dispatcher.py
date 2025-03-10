import asyncio
import inspect
import logging
import traceback
from typing import Annotated, Any, Callable, Dict, List, Optional, Set, Tuple, Type, get_origin

from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.displayers.EventDisplayer import EventDisplayer
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.nats.context.run.RunContext import RunContext
from aihub_lib.nats.context.thread.ThreadContext import ThreadContext
from aihub_lib.nats.events import BaseEvent, ControlEvent, DisplayEvent, ExceptionEvent, StartEvent, StopEvent
from aihub_lib.nats.events.agent_in_the_loop.request.AgentInTheLoopRequestEvent import AgentInTheLoopRequestEvent
from aihub_lib.nats.events.human_in_the_loop import HumanInTheLoopRequestEvent
from aihub_lib.nats.publishers.JSPublisher import JSPublisher
from aihub_lib.nats.publishers.NCPublisher import NCPublisher
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

from aihub_agent.agents.abstract.Agent import Agent
from aihub_agent.dispatchers.stores.event.JetStreamEventStore import JetStreamEventStore
from aihub_agent.dispatchers.stores.step.StepStore import DistributedStepStore
from aihub_agent.i18n.AgentLocaleHandler import AgentLocaleHandler
from aihub_agent.tracing.coordinators.RunTraceCoordinator import RunTraceCoordinator
from aihub_agent.workflow.annotations.custom_types.ListOfSize import ListOfSize

logger = logging.getLogger(__name__)


class Dispatcher:
    """
    The Dispatcher orchestrates the execution of workflow steps within an agent run. It acts as the
    central coordinator that listens to events, determines which steps should fire, injects the right
    parameters into those steps, and handles the lifecycle of runs (start, error, stop).

    ### Why the Dispatcher?
    A workflow often involves multiple steps that depend on certain events. The Dispatcher ties all these
    concepts together:
    - It receives events (like `StartEvent`, `StopEvent`, custom `ControlEvent`s).
    - Finds which steps are "ready" to execute based on available events and step definitions.
    - Fetches needed contextual data (thread/run contexts, previous events) and constructs the arguments
      for the steps.
    - Executes steps and publishes any resulting events, updating the run’s state as needed.

    By centralizing these responsibilities, the Dispatcher ensures consistent, reliable orchestration of
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
       The Dispatcher enforces these rules in `is_step_ready` and `execute_step`.

    3. **Context and State Management:**
       The Dispatcher uses `RunContext` and `ThreadContext` for state persistence. It interacts with `DistributedEventStore`
       and `DistributedStepStore` to track event histories and step execution counts across distributed environments.

    4. **Tracing and Telemetry:**
       Through `RunTraceCoordinator`, it logs start/end times of runs and steps, aiding observability.

    ### Lifecycle
    A typical flow might be:
    - On a `StartEvent`, the run is initialized, contexts are set, tracing begins.
    - Incoming events trigger checks for steps that can run.
    - Steps run and produce new events, potentially enabling further steps.
    - On completion (`StopEvent`), the Dispatcher cleans up run-level data.

    ### Integration with Other Components
    - **Agent & Steps:** The Dispatcher uses the agent’s defined steps and their annotated metadata (like required events).
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
        self.agent = agent
        self.agent_config = agent_config
        self.nc = nc
        self.js = js
        self.redis = redis
        self.topic_manager = topic_manager
        self.locale_handler = locale_handler

        self.nc_publisher = NCPublisher(self.nc)
        self.js_publisher = JSPublisher(self.js)
        self.event_store = JetStreamEventStore(self.nc, self.js, self.topic_manager)
        self.step_store = DistributedStepStore(redis)
        self.tracer = RunTraceCoordinator(self.nc)
        self.step_configs = agent_config.get_step_configs()

        # Initialization flag
        self._initialized = False
        self._init_lock = asyncio.Lock()

    async def start(self):
        """
        Initialize the dispatcher by starting the event store.
        This must be called before the dispatcher can process any events.
        """
        async with self._init_lock:
            if self._initialized:
                return

            # Initialize the event store
            await self.event_store.start()
            self._initialized = True
            logger.info("Dispatcher initialized and ready to process events")

    async def stop(self):
        await self.event_store.stop()

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
        if not self._initialized:
            await self.start()

        logger.debug(f"Handling event {event.__class__.__name__} for subject {topic}")

        await self.event_store.ensure_event_stored(topic.run_id, event)

        # Retrieve contexts (run and thread)
        run_context = RunContext(self.redis, topic.thread_id, topic.run_id)
        thread_context = ThreadContext(self.redis, topic.thread_id)

        if isinstance(event, StartEvent):
            logger.debug(f"Handling StartEvent: {event.__class__.__name__}")
            telemetry_headers = self.tracer.trace_run_start(topic, event)
            await run_context.set("telemetry_headers", telemetry_headers)

            # Store any initial data from the StartEvent into run_context
            event_data = event.to_context_dict()
            for key, value in event_data.items():
                logger.debug(f"Setting key '{key}' in run_context to '{value}'")
                await run_context.set(key, value)

        if isinstance(event, StopEvent):
            logger.debug(f"Handling StopEvent: {event.__class__.__name__}")
            # Clean up run-specific data
            await run_context.delete_all()
            await self.event_store.delete_all(topic.run_id)
            await self.step_store.delete_all(topic.run_id)
            return

        if isinstance(event, ExceptionEvent):
            logger.debug(f"Handling ExceptionEvent: {event.__class__.__name__}")
            # Mark run as crashed so no further steps are executed
            await self.step_store.mark_run_as_crashed(topic.run_id)
            return

        # Determine which steps need to be executed due to this event
        steps = self.agent.get_steps_waiting_for_event(type(event))
        for step_method in steps:
            logger.debug(f"Checking step '{step_method.__name__}' for readiness")
            input_events = getattr(step_method, "_input_events", set())
            input_event_class_names = [event_type.__name__ for event_type in input_events]
            events = await self.event_store.get_events_of_multiple_types(
                topic.run_id, input_event_class_names, until=event.created_at
            )
            if await self.is_step_ready(event, step_method, events, run_context, thread_context, topic):
                logger.debug(f"Triggering step '{step_method.__name__}' due to event '{event.__class__.__name__}'")
                asyncio.create_task(self.execute_step(event, step_method, events, run_context, thread_context, topic))

    async def is_step_ready(
        self,
        trigger_event: Annotated[ControlEvent, "The event that caused this step to trigger."],
        step_method: Annotated[Callable, "The step method to check."],
        events: Annotated[Dict[str, List[ControlEvent]], "All events for this run, keyed by event_type_name."],
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
        if await self.step_store.is_run_crashed(topic.run_id):
            logger.warning(f"Run {topic.run_id} is crashed; skipping step.")
            return False

        max_executions = getattr(step_method, "_max_executions_per_run", None)
        if max_executions is not None:
            execution_count = await self.step_store.get_execution_count(topic.run_id, step_method.__name__)
            if execution_count >= max_executions:
                logger.debug(
                    f"[{step_method.__name__}] Max executions reached ({execution_count}/{max_executions}), skipping."
                )
                return False

        input_event_mapping: Dict[str, Set[Type[ControlEvent]]] = getattr(step_method, "_input_event_mapping", {})
        parameter_optional_map: Dict[str, bool] = getattr(step_method, "_parameter_optional_map", {})
        size_requirements: Dict[str, Optional[int]] = getattr(step_method, "_size_requirements", {})
        precondition_fn: Optional[Callable[..., bool]] = getattr(step_method, "_precondition_fn", None)

        # For each parameter, check if we have enough events
        for argument_name, event_types in input_event_mapping.items():
            logger.debug(f"[{step_method.__name__}] Checking argument '{argument_name}' for event types {event_types}")
            required_size = size_requirements.get(argument_name)
            is_optional = parameter_optional_map.get(argument_name, False)

            available_events_count = sum(len(events.get(event_type.__name__, [])) for event_type in event_types)

            # If a fixed size is required, verify count
            if required_size is not None and available_events_count < required_size:
                logger.debug(
                    f"[{step_method.__name__}] Not enough events for '{argument_name}'. "
                    f"Needed {required_size}, got {available_events_count}."
                )
                return False
            elif required_size is None and not available_events_count and not is_optional:
                # Required events not found
                logger.debug(f"[{step_method.__name__}] Missing required argument '{argument_name}' events.")
                return False
            elif not available_events_count and is_optional:
                logger.debug(
                    f"[{step_method.__name__}] Optional arg '{argument_name}' not provided, continuing anyway."
                )

        if precondition_fn:
            _, precondition_args = await self._build_method_kwargs(
                trigger_event, precondition_fn, events, run_context, thread_context, topic
            )
            is_ready = precondition_fn(**precondition_args)
            if not is_ready:
                logger.debug(f"[{step_method.__name__}] Ready function returned False, skipping.")
                return False

        logger.debug(f"[{step_method.__name__}] All input requirements satisfied.")
        return True

    @staticmethod
    def _get_event_value(
        param: Annotated[inspect.Parameter, "A parameter of the step method."],
        step_method: Annotated[Callable, "The step method we're preparing arguments for."],
        events: Annotated[
            Dict[str, List[ControlEvent]],
            "All events for this run, keyed by event_type_name.",
        ],
        trigger_event: Annotated[ControlEvent, "The event that triggered this step execution."],
    ) -> Optional[Any]:
        """
        Finds the appropriate value for a given step parameter.

        Logic:
        - Gathers all events that match the parameter's required event types.
        - If a fixed-size list is required, returns a `ListOfSize` if exact count matches.
        - If a list is required (but not fixed-size), returns all matching events.
        - If a single event is expected, returns the trigger event if it matches, else the latest matching event.

        Returns None if no suitable event is found and the parameter is optional.
        """
        event_types = step_method._input_event_mapping.get(param.name, set())
        size_requirements = getattr(step_method, "_size_requirements", {})
        required_size = size_requirements.get(param.name)

        # Gather all matching events
        all_matching_events: List[ControlEvent] = []
        for event_type in event_types:
            event_list = events.get(event_type.__name__, [])
            all_matching_events.extend(event_list)

        if not all_matching_events:
            return None

        # Sort events by creation time for deterministic ordering
        all_matching_events.sort(key=lambda x: x.created_at)

        # Handle fixed-size requirements
        if required_size is not None:
            if len(all_matching_events) == required_size:
                return ListOfSize(all_matching_events[-required_size:], required_size)
            return None

        # Handle lists
        elif get_origin(param.annotation) in (list, List):
            return all_matching_events

        # Handle single event
        else:
            # If the trigger event is among them, prefer it
            if trigger_event.event_id in [evt.event_id for evt in all_matching_events]:
                return trigger_event
            # Else return the latest available event
            return all_matching_events[-1]

    async def execute_step(
        self,
        trigger_event: Annotated[ControlEvent, "The event that caused this step to trigger."],
        step_method: Annotated[Callable, "The step method to execute."],
        events: Annotated[Dict[str, List[ControlEvent]], "All events for this run, keyed by event_type_name."],
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
            await self.step_store.increment_execution_count(topic.run_id, step_method.__name__)

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
            topic.run_id, step_method.__name__, all_input_events
        )
        if duplicated_run:
            logger.debug(f"Skipping step '{step_method.__name__}' as it has already been called with the same events.")
            return

        await self.step_store.report_run_with_events(topic.run_id, step_method.__name__, all_input_events)

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
                logger.error(f"Error executing step '{step_method.__name__}': {e}")
                traceback.print_exc()
                return

            # If the step returns events, publish them
            if result:
                if not isinstance(result, list):
                    result = [result]

                await self.tracer.trace_step_stop(step_span, result)

                for event in result:
                    if isinstance(event, HumanInTheLoopRequestEvent):
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

                    if isinstance(event, AgentInTheLoopRequestEvent):
                        logger.debug(f"Handling special event: AgentInTheLoopRequestEvent: {event}")
                        await self.trigger_agent_in_the_loop(event, topic)

                    await self.publish_event(event, topic)

    async def _build_method_kwargs(
        self,
        trigger_event: Annotated[ControlEvent, "The event that caused this step to trigger."],
        method: Annotated[Callable, "The method to prepare the args for."],
        events: Annotated[Dict[str, List[ControlEvent]], "All events for this run, keyed by event_type_name."],
        run_context: Annotated[RunContext, "Per-run context for state and configuration."],
        thread_context: Annotated[ThreadContext, "Per-thread context for longer-lived state."],
        topic: Annotated[AgentTopic, "Topic info for the current run and thread."],
    ) -> Tuple[List[ControlEvent], Dict[str, Any]]:
        kwargs: Dict[str, Any] = {}
        step_signature = inspect.signature(method)
        parameter_optional_map = getattr(method, "_parameter_optional_map", {})
        all_input_events: List[ControlEvent] = []
        # Prepare arguments
        for param in step_signature.parameters.values():
            if param.name == "self":
                continue

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
                continue

            # Handle event parameters
            event_value = self._get_event_value(param, method, events, trigger_event)
            if event_value is not None or parameter_optional_map.get(param.name, False):
                kwargs[param.name] = event_value
            else:
                raise ValueError(f"[{method.__name__}] Missing required event for parameter '{param.name}'")

            if isinstance(event_value, list):
                all_input_events.extend([event for event in event_value if isinstance(event, ControlEvent)])
            elif isinstance(event_value, ControlEvent):
                all_input_events.append(event_value)
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
        response_event_type = aitl_request_event.response
        exception_event_type = aitl_request_event.exception

        start_event = aitl_request_event.start_event

        async def convert_event_to_agent_in_the_loop_response(aitl_event: BaseEvent, aitl_topic: Topic):
            if isinstance(aitl_event, StopEvent):
                aitl_response = response_event_type(stop_event=aitl_event)
                logger.debug(f"Received Agent in the Loop StopEvent: {aitl_response}, stopping subscriber.")
                await event_subscriber.stop()
                await self.publish_event(aitl_response, topic)
            if isinstance(aitl_event, ExceptionEvent):
                aitl_exception = exception_event_type(exception_event=aitl_event)
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
        if isinstance(event, ControlEvent):
            subject = topic_manager.get_subject_for_control_event_in_thread(event.__class__.__name__, event.event_id)
            await self.js_publisher.publish_event(event, subject)
        if isinstance(event, DisplayEvent):
            subject = topic_manager.get_subject_for_display_event_in_thread(event.__class__.__name__, event.event_id)
            await self.nc_publisher.publish_event(event, subject)
