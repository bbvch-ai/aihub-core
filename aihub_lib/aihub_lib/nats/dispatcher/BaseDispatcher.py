import abc
import asyncio
import inspect
import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Annotated, Any, get_origin

from nats.aio.client import Client as NATS
from nats.js import JetStreamContext
from redis.asyncio import Redis

from aihub_lib.nats.dispatcher.stores.event.JetStreamEventStore import JetStreamEventStore
from aihub_lib.nats.dispatcher.stores.step.StepStore import StepStore
from aihub_lib.nats.events import BaseEvent
from aihub_lib.nats.publishers.JSPublisher import JSPublisher
from aihub_lib.nats.publishers.NCPublisher import NCPublisher
from aihub_lib.nats.topic_managers.AbstractStreamTopicManager import AbstractStreamTopicManager
from aihub_lib.nats.topics import Topic
from aihub_lib.nats.workflow.annotations.custom_types.ListOfSize import ListOfSize
from aihub_lib.nats.workflow.DispatchableWorkflow import DispatchableWorkflow

logger = logging.getLogger(__name__)


@dataclass
class EventsAndKwargs:
    """
    Holds the step method input keyword arguments and the events mentioned in said kwargs
    """

    events: list[BaseEvent]
    kwargs: dict[str, Any]


class BaseDispatcher(abc.ABC):
    """
    The dispatcher is where the actual magic happens! Given a dispatchable workflow, the dispatcher creates
    the appropriate connection to jetstream to ensure all events published towards this workflow entity are stored
    and ready to access. It also handles event replaying, ensuring that all historical events are available
    as well.
    The dispatcher then listens to incoming events. For each new event, it checks for each method in the workflow
    whether the conditions to run this methods are satisfied, e.g. whether all the events specified as
    method arguments are available. If so, it triggers the execution of this method asynchronously and. After
    the execution completed, the dispatcher publishes the new events that were created by this method as well,
    potentially triggering new method executions.

    Hence, the four most important functions within a dispatcher are:
    - `handle_event`: Called whenever a new event arrives.
    - `is_step_ready`: Checks if a step can be run given the current state (events available, etc.).
    - `execute_step`: Triggers the execution of a step asynchronously.
    - `publish_event`: Publishes the returned events from a step.

    Note that a dispatcher works in a completely distributed manner. Hence, the class itself does NOT hold any state.
    Why?
    Well, even for the exact same workflow class and workflow instance, multiple dispatchers can exist.
    JetStream will do load balancing and send each event to exactly one dispatcher. Hence, the dispatchers need
    to share state, even when they are hosted on different servers in different countries. This is why we always
    rely on JetStream or Redis for state and never on class or instance variables on the dispatcher itself.
    """

    def __init__(
        self,
        nc: Annotated[NATS, "NATS client for messaging."],
        js: Annotated[
            JetStreamContext,
            "JetStream context for persistent storage and event streams.",
        ],
        redis: Annotated[Redis, "Redis client for distributed storage."],
        topic_manager: Annotated[AbstractStreamTopicManager, "Manages event subjects."],
        topic: Annotated[type[Topic], "Topic under which these events were published"],
        dispatch_entity_name: Annotated[str, "Name of the entity that this dispatcher is responsible for."],
    ):
        self.nc = nc
        self.js = js
        self.redis = redis

        self.topic_manager = topic_manager
        self.topic = topic

        self.nc_publisher = NCPublisher(self.__class__.__name__, self.nc)
        self.js_publisher = JSPublisher(f"{dispatch_entity_name}Dispatcher", self.js)

        self.event_store = JetStreamEventStore(
            self.nc,
            self.js,
            self.topic_manager,
            self.topic,
        )
        self.step_store = StepStore(redis)

        # Initialization flag
        self._initialized = False
        self._init_lock = asyncio.Lock()

        self._background_tasks: set[asyncio.Task] = set()

    @abc.abstractmethod
    async def handle_event(
        self,
        event: Annotated[BaseEvent, "The incoming control event to handle."],
        topic: Annotated[Topic, "The parsed topic of the event."],
    ):
        """
        This method is called each time an event is received by this workflow instance. Hence, this method
        is potentially called A LOT, like, for some agents, hundreds of times per second.
        The primary responsibility of this method is to handle special kinds of events, like StartEvent or StopEvent
        that mark setup or teardown of a run, and looping through all workflow methods, checking for each of them
        whether they can be executed given the current state of the run. If so, it triggers the execution of this
        method.
        Note that in the base dispatcher, there is not much logic. It simply ensures that the dispatcher is
        initialized and that the event is stored in the event store.
        All logic regarding setup/teardown/triggering must be implemented in subclasses.
        """
        if not self._initialized:
            await self.start()

        logger.debug(f"Handling event {event.event_name} for subject {topic}")

        # Add the event directly to the store since we already have it
        # This avoids timing issues with waiting for a second delivery via subscription
        self.event_store._add_event_to_store(topic.execution_context_id, event)

    @abc.abstractmethod
    async def is_step_ready(
        self,
        step_method: Annotated[Callable, "The step method to check."],
        events: Annotated[dict[str, list[BaseEvent]], "All events for this run, keyed by event name."],
        topic: Annotated[Topic, "Topic info for the current process."],
    ) -> bool:
        """
        This method must decide - for a given step methods and a set of events received so far - whether the step
        can be executed. It should return True if the step can be executed, False otherwise.
        """
        pass

    @abc.abstractmethod
    async def execute_step(
        self,
        trigger_event: Annotated[BaseEvent, "The event that caused this step to trigger."],
        step_method: Annotated[Callable, "The step method to execute."],
        events: Annotated[dict[str, list[BaseEvent]], "All events for this run, keyed by event name."],
        topic: Annotated[Topic, "Topic info for the current process."],
    ):
        """
        This method should execute the step method asynchronously and publish the events returned by the
        step method to jetstream.
        """
        pass

    @abc.abstractmethod
    async def publish_event(
        self,
        event: Annotated[BaseEvent, "The event to publish."],
        topic: Annotated[Topic, "Current process topic context."],
    ):
        """Publishes an event to jetstream."""
        pass

    async def start(self):
        """
        Ensures that the event store holds all past events for this workflow and hence has a commplete state.
        """
        async with self._init_lock:
            if self._initialized:
                return

            # Initialize the event store
            await self.event_store.start()
            self._initialized = True
            logger.info("Dispatcher initialized and ready to process events")

    async def stop(self):
        if not self._initialized:
            return

        # Stop the event store
        await self.event_store.stop()
        self._initialized = False
        logger.info("Dispatcher stopped")

    async def _step_meets_basic_execution_requirements(
        self,
        step_method: Annotated[Callable, "The step method to check."],
        events: Annotated[dict[str, list[BaseEvent]], "All events for this run, keyed by event name."],
        topic: Annotated[Topic, "Topic info for the current execution context."],
    ) -> bool:
        """
        Checks if a step can be run given the current state (events available, max executions, etc.).

        It verifies:
        - The run hasn't crashed.
        - All required input events are available in the needed quantities.

        Returns True if the step can execute, False otherwise.
        """
        if await self.step_store.is_execution_context_crashed(topic.execution_context_id):
            logger.warning(f"Run {topic.execution_context_id} is crashed; skipping step.")
            return False

        input_event_mapping: dict[str, set[type[BaseEvent]]] = getattr(
            step_method, DispatchableWorkflow.INPUT_EVENT_MAPPING_ANNOTATION, {}
        )
        parameter_optional_map: dict[str, bool] = getattr(
            step_method, DispatchableWorkflow.PARAMETER_OPTIONAL_MAP_ANNOTATION, {}
        )
        size_requirements: dict[str, int | None] = getattr(
            step_method, DispatchableWorkflow.SIZE_REQUIREMENT_ANNOTATION, {}
        )

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
        trigger_event: Annotated[BaseEvent, "The event that caused this step to trigger."],
        method: Annotated[Callable, "The method to prepare the args for."],
        events: Annotated[dict[str, list[BaseEvent]], "All events for this run, keyed by event name."],
    ) -> EventsAndKwargs:
        kwargs: dict[str, Any] = {}
        step_signature = inspect.signature(method)
        parameter_optional_map = getattr(method, DispatchableWorkflow.PARAMETER_OPTIONAL_MAP_ANNOTATION, {})
        all_input_events: list[BaseEvent] = []

        for param in step_signature.parameters.values():
            if param.name == "self":
                continue

            event_value = self._get_event_value(param, method, events, trigger_event)

            # If parameter is optional, we can assign in all cases (None or actual Event)
            if parameter_optional_map.get(param.name, False):
                kwargs[param.name] = event_value

            if event_value is None:
                continue

            kwargs[param.name] = event_value

            if isinstance(event_value, list | tuple | ListOfSize):
                all_input_events.extend([event for event in event_value if event.is_control_event])
            elif isinstance(event_value, BaseEvent) and event_value.is_control_event:
                all_input_events.append(event_value)

        return EventsAndKwargs(
            events=all_input_events,
            kwargs=kwargs,
        )

    @staticmethod
    def _get_event_value(
        param: Annotated[inspect.Parameter, "A parameter of the step method."],
        step_method: Annotated[Callable, "The step method we're preparing arguments for."],
        events: Annotated[
            dict[str, list[BaseEvent]],
            "All events for this run, keyed by event name.",
        ],
        trigger_event: Annotated[BaseEvent, "The event that triggered this step execution."],
    ) -> Any | None:
        """
        Finds the appropriate value for a given step parameter.

        Logic:
        - Gathers all events that match the parameter's required event types.
        - If a fixed-size list is required, returns a `ListOfSize` if exact count matches.
        - If a list is required (but not fixed-size), returns all matching events.
        - If a single event is expected, returns the trigger event if it matches, else the latest matching event.

        Returns None if no suitable event is found.
        """
        event_classes = getattr(step_method, DispatchableWorkflow.INPUT_EVENT_MAPPING_ANNOTATION, {}).get(
            param.name, set()
        )
        size_requirements = getattr(step_method, DispatchableWorkflow.SIZE_REQUIREMENT_ANNOTATION, {})
        required_size = size_requirements.get(param.name)

        # Gather all matching events
        all_matching_events: list[BaseEvent] = []
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
        elif get_origin(param.annotation) in (list, list):
            return all_matching_events

        # Handle single event
        else:
            # If the trigger event is among them, prefer it
            if trigger_event.event_id in [evt.event_id for evt in all_matching_events]:
                return trigger_event
            # Else return the latest available event
            return all_matching_events[-1]
