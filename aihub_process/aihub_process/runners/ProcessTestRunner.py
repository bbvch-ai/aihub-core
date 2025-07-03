from asyncio import sleep
from contextlib import asynccontextmanager
from typing import Annotated, AsyncGenerator, List, Optional, Type

from aihub_lib.infrastructure.RedisConfig import RedisConfig
from aihub_lib.nats.events import (
    BaseEvent,
    DiscoveryRequestEvent,
    ProcessExceptionEvent,
    ProcessStartEvent,
    ProcessStopEvent,
)
from aihub_lib.nats.events.discovery import ProcessDiscoveryResponseEvent
from aihub_lib.nats.NatsConfig import NatsConfig
from aihub_lib.nats.subscribers.JSSubscriber import JSSubscriber
from aihub_lib.nats.subscribers.process.ProcessNCSubscriber import ProcessNCSubscriber
from aihub_lib.nats.topic_managers.process.ProcessInstanceTopicManager import ProcessInstanceTopicManager
from aihub_lib.nats.topic_managers.process.ProcessTopicManager import ProcessTopicManager
from aihub_lib.nats.topics import ProcessTopic, Topic
from aihub_lib.processes.ProcessConfig import ProcessConfig
from openai import BaseModel

from aihub_process.agentic_processes.AgenticProcess import AgenticProcess
from aihub_process.runners.ProcessRunner import ProcessRunner


class ObservedEvent(BaseModel):
    """
    Wraps an observed event along with its associated topic, making it easier to inspect what events
    have passed through the system during tests.
    """

    event: BaseEvent
    topic: Topic


class ProcessTestRunner(ProcessRunner):
    """
    A specialized runner intended for testing processs. It extends `ProcessRunner` by:
    - Observing events published by the process and storing them for assertions in tests.
    - Providing a `test_run` context manager that sets up a test environment, including
      event subscriptions and automatic cleanup after a delay.
    - Utilities to quickly check if certain event classes (ProcessStart/ProcessStop/ProcessException) have been emitted,
      and to retrieve all events of a particular type.
    """

    def __init__(
        self,
        process_type: Type[AgenticProcess],
        process_config: ProcessConfig,
        locale_paths: Optional[List[str]] = None,
    ):
        super().__init__(
            servers=[NatsConfig().NATS_ENDPOINT],
            redis_url=RedisConfig().REDIS_URL,
            process_type=process_type,
            process_config=process_config,
            locale_paths=locale_paths,
        )
        self.test_event_subscriber: Optional[JSSubscriber] = None
        self.observed_events: List[ObservedEvent] = []

        self.observe_discovery_event_subscriber: Optional[ProcessNCSubscriber] = None
        self.observe_discovery_response_event_subscriber: Optional[ProcessNCSubscriber] = None

    async def observe_event(self, event: BaseEvent, topic: Topic):
        """
        Handler for observed events. Whenever an event is published to the run’s thread,
        this handler stores it in self.observed_events.
        """
        self.observed_events.append(ObservedEvent(event=event, topic=topic))

    @asynccontextmanager
    async def test_run(self, delay_before_stop: int = 1) -> AsyncGenerator[None, None]:
        await self.test_run_start()
        yield
        await sleep(delay_before_stop)
        await self.test_run_stop()

    async def test_run_start(self):
        await self.start()

        self.test_event_subscriber = ProcessNCSubscriber.for_all_process_events(
            nc=self.nc,
            topic_manager=ProcessInstanceTopicManager(
                process_class=self.process_class,
                process_id=self.process_config.process_id,
            ),
            handler=self.observe_event,
        )
        await self.test_event_subscriber.start()

        self.observe_discovery_event_subscriber = ProcessNCSubscriber.for_process_discovery_request_events(
            nc=self.nc,
            topic_manager=ProcessTopicManager(),
            handler=self.observe_event,
        )
        await self.observe_discovery_event_subscriber.start()

        self.observe_discovery_response_event_subscriber = ProcessNCSubscriber.for_process_discovery_request_events(
            nc=self.nc,
            topic_manager=ProcessTopicManager(),
            handler=self.observe_event,
        )
        await self.observe_discovery_response_event_subscriber.start()

    async def test_run_stop(self):
        await self.test_event_subscriber.stop()
        await self.observe_discovery_event_subscriber.stop()
        await self.stop()

    @property
    def has_start_event(self) -> bool:
        """Check if a ProcessStartEvent was observed."""
        return any(isinstance(event.event, ProcessStartEvent) for event in self.observed_events)

    def get_start_event(self) -> ProcessStartEvent:
        """
        Returns the first observed ProcessStartEvent.
        Raises StopIteration if no ProcessStartEvent was observed.
        """
        return next(event.event for event in self.observed_events if isinstance(event.event, ProcessStartEvent))

    @property
    def has_stop_event(self) -> bool:
        """Check if a ProcessStopEvent was observed."""
        return any(isinstance(event.event, ProcessStopEvent) for event in self.observed_events)

    @property
    def has_exception_event(self) -> bool:
        """Check if an ProcessExceptionEvent was observed."""
        return any(isinstance(event.event, ProcessExceptionEvent) for event in self.observed_events)

    @property
    def has_discovery_request_event(self) -> bool:
        """Check if a DiscoveryRequestEvent was observed."""
        return any(isinstance(event.event, DiscoveryRequestEvent) for event in self.observed_events)

    @property
    def has_own_process_discovery_response_event(self) -> bool:
        """Check if an ProcessDiscoveryResponseEvent with the process's class and ID was observed."""
        return any(
            isinstance(event.event, ProcessDiscoveryResponseEvent)
            and event.event.process_class == self.process_class
            and event.event.process_id == self.process_config.process_id
            for event in self.observed_events
        )

    def get_topics(
        self,
        event_class: Type[BaseEvent],
        exact: Annotated[bool, "Must the event be an exact match or is subclass okay?"] = False,
    ) -> List[ProcessTopic]:
        """Returns the topics of all observed events of the specified class, if any are ProcessTopic."""
        return [
            ev.topic
            for ev in self.observed_events
            if isinstance(ev.event, event_class)
            and (not exact or event_class.event_name_from_class() == ev.event.event_name)
            and isinstance(ev.topic, ProcessTopic)
        ]

    def get_events_of_class(
        self,
        event_class: Type[BaseEvent],
        exact: Annotated[bool, "Must the event be an exact match or is subclass okay?"] = False,
    ) -> List[BaseEvent]:
        """Returns all observed events of the specified class."""
        return [
            ev.event
            for ev in self.observed_events
            if isinstance(ev.event, event_class)
            and (not exact or event_class.event_name_from_class() == ev.event.event_name)
        ]

    def has_event_of_class(
        self,
        event_class: Type[BaseEvent],
        exact: Annotated[bool, "Must the event be an exact match or is subclass okay?"] = False,
    ) -> bool:
        """Check if any event of the specified class was observed."""
        return len(self.get_events_of_class(event_class, exact)) > 0

    def get_event_of_class(
        self,
        event_class: Type[BaseEvent],
        exact: Annotated[bool, "Must the event be an exact match or is subclass okay?"] = False,
    ) -> BaseEvent:
        """
        Returns the first observed event of the specified class.
        Raises StopIteration if no such event is found.
        """
        events_of_class = self.get_events_of_class(event_class, exact)
        if len(events_of_class) > 0:
            return events_of_class[0]
        raise StopIteration(f"No event of class {event_class.event_name_from_class()} was observed")

    async def wait_for_event(
        self,
        event_class: Type[BaseEvent],
        timeout: float = 60.0,
        interval: float = 0.1,
    ) -> BaseEvent:
        """
        Wait until an event of the specified class is observed or until the timeout is reached.
        """
        max_attempts = int(timeout / interval)  # Maximum number of attempts based on the timeout
        attempts = 0

        while not self.has_event_of_class(event_class):
            if attempts >= max_attempts:
                raise TimeoutError(f"Timeout waiting for event of class {event_class.event_name_from_class()}")
            attempts += 1
            await sleep(interval)

        return self.get_event_of_class(event_class)
