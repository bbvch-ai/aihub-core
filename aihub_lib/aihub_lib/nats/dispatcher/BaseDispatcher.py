import asyncio
import inspect
import logging
from typing import Annotated, Any, Callable, Dict, List, Optional, Set, Tuple, Type, get_origin

from nats.aio.client import Client as NATS
from nats.js import JetStreamContext
from redis.asyncio import Redis

from aihub_lib.nats.dispatcher.stores.event.JetStreamEventStore import JetStreamEventStore
from aihub_lib.nats.dispatcher.stores.step.StepStore import StepStore
from aihub_lib.nats.events import BaseEvent, ControlEvent
from aihub_lib.nats.publishers.JSPublisher import JSPublisher
from aihub_lib.nats.publishers.NCPublisher import NCPublisher
from aihub_lib.nats.topic_managers.AbstractStreamTopicManager import AbstractStreamTopicManager
from aihub_lib.nats.topics import Topic
from aihub_lib.nats.workflow.annotations.custom_types.ListOfSize import ListOfSize

logger = logging.getLogger(__name__)


class BaseDispatcher:
    def __init__(
        self,
        nc: Annotated[NATS, "NATS client for messaging."],
        js: Annotated[
            JetStreamContext,
            "JetStream context for persistent storage and event streams.",
        ],
        redis: Annotated[Redis, "Redis client for distributed storage."],
        topic_manager: Annotated[AbstractStreamTopicManager, "Manages event subjects."],
        topic: Annotated[Type[Topic], "Topic under which these events were published"],
    ):
        self.nc = nc
        self.js = js
        self.redis = redis

        self.topic_manager = topic_manager
        self.topic = topic

        self.nc_publisher = NCPublisher(self.nc)
        self.js_publisher = JSPublisher(self.js)

        self.event_store = JetStreamEventStore(self.nc, self.js, self.topic_manager, self.topic)
        self.step_store = StepStore(redis)

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
        topic: Annotated[Topic, "The parsed topic of the event."],
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

        logger.debug(f"Handling event {event.event_name} for subject {topic}")

        await self.event_store.ensure_event_stored(topic.execution_context_id, event)

    async def step_meets_basic_execution_requirements(
        self,
        step_method: Annotated[Callable, "The step method to check."],
        events: Annotated[Dict[str, List[ControlEvent]], "All events for this run, keyed by event name."],
        topic: Annotated[Topic, "Topic info for the current execution context."],
    ) -> bool:
        """
        Checks if a step can be run given the current state (events available, max executions, etc.).

        It verifies:
        - The run hasn't crashed.
        - The step hasn't exceeded its max execution count.
        - All required input events are available in the needed quantities.

        Returns True if the step can execute, False otherwise.
        """
        if await self.step_store.is_execution_context_crashed(topic.execution_context_id):
            logger.warning(f"Run {topic.execution_context_id} is crashed; skipping step.")
            return False

        max_executions = getattr(step_method, "_max_executions_per_run", None)
        if max_executions is not None:
            execution_count = await self.step_store.get_execution_count(
                topic.execution_context_id, step_method.__name__
            )
            if execution_count >= max_executions:
                logger.debug(
                    f"[{step_method.__name__}] Max executions reached ({execution_count}/{max_executions}), skipping."
                )
                return False

        input_event_mapping: Dict[str, Set[Type[ControlEvent]]] = getattr(step_method, "_input_event_mapping", {})
        parameter_optional_map: Dict[str, bool] = getattr(step_method, "_parameter_optional_map", {})
        size_requirements: Dict[str, Optional[int]] = getattr(step_method, "_size_requirements", {})

        # For each parameter, check if we have enough events
        for argument_name, event_classes in input_event_mapping.items():
            logger.debug(
                f"[{step_method.__name__}] Checking argument '{argument_name}' for event types {event_classes}"
            )
            required_size = size_requirements.get(argument_name)
            is_optional = parameter_optional_map.get(argument_name, False)

            available_events_count = sum(
                len(events.get(event_class.event_name_from_class(), [])) for event_class in event_classes
            )

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

        logger.debug(f"[{step_method.__name__}] All base input requirements satisfied.")
        return True

    async def _build_event_kwargs(
        self,
        trigger_event: Annotated[ControlEvent, "The event that caused this step to trigger."],
        method: Annotated[Callable, "The method to prepare the args for."],
        events: Annotated[Dict[str, List[ControlEvent]], "All events for this run, keyed by event name."],
    ) -> Tuple[List[ControlEvent], Dict[str, Any]]:
        kwargs: Dict[str, Any] = {}
        step_signature = inspect.signature(method)
        parameter_optional_map = getattr(method, "_parameter_optional_map", {})
        all_input_events: List[ControlEvent] = []

        for param in step_signature.parameters.values():
            if param.name == "self":
                continue

            event_value = self._get_event_value(param, method, events, trigger_event)
            if event_value is None:
                continue

            if parameter_optional_map.get(param.name, False):
                kwargs[param.name] = event_value

            if isinstance(event_value, list):
                all_input_events.extend([event for event in event_value if event.is_control_event])
            elif isinstance(event_value, BaseEvent) and event_value.is_control_event:
                all_input_events.append(event_value)

        return all_input_events, kwargs

    @staticmethod
    def _get_event_value(
        param: Annotated[inspect.Parameter, "A parameter of the step method."],
        step_method: Annotated[Callable, "The step method we're preparing arguments for."],
        events: Annotated[
            Dict[str, List[ControlEvent]],
            "All events for this run, keyed by event name.",
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
        event_classes = step_method._input_event_mapping.get(param.name, set())
        size_requirements = getattr(step_method, "_size_requirements", {})
        required_size = size_requirements.get(param.name)

        # Gather all matching events
        all_matching_events: List[ControlEvent] = []
        for event_class in event_classes:
            event_list = events.get(event_class.event_name_from_class(), [])
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
