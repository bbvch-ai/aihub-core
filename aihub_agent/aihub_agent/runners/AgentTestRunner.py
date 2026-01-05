from asyncio import sleep
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Annotated

from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.infrastructure.nats.NatsSettings import NatsSettings
from aihub_lib.infrastructure.redis.RedisSettings import RedisSettings
from aihub_lib.nats.events import BaseEvent
from aihub_lib.nats.events.control import ExceptionEvent, StartEvent, StopEvent
from aihub_lib.nats.events.discovery.agent.AgentClassDiscoveryResponseEvent import AgentClassDiscoveryResponseEvent
from aihub_lib.nats.events.discovery.ClassDiscoveryRequestEvent import ClassDiscoveryRequestEvent
from aihub_lib.nats.publishers.JSPublisher import JSPublisher
from aihub_lib.nats.streams.StreamManager import StreamManager
from aihub_lib.nats.subscribers.agent.AgentNCSubscriber import AgentNCSubscriber
from aihub_lib.nats.subscribers.JSSubscriber import JSSubscriber
from aihub_lib.nats.topic_managers.agents.AgentClassTopicManager import AgentClassTopicManager
from aihub_lib.nats.topic_managers.agents.AgentInstanceTopicManager import AgentInstanceTopicManager
from aihub_lib.nats.topic_managers.agents.AgentThreadTopicManager import AgentThreadTopicManager
from aihub_lib.nats.topic_managers.agents.AgentTopicManager import AgentTopicManager
from aihub_lib.nats.topics import Topic
from aihub_lib.nats.topics.agents.AgentInstanceTopic import AgentInstanceTopic
from aihub_lib.nats.topics.agents.PartialAgentTopic import PartialAgentTopic
from bson import ObjectId
from pydantic import BaseModel

from aihub_agent.agents.Agent import Agent
from aihub_agent.runners.AgentRunner import AgentRunner


class ObservedEvent(BaseModel):
    """
    Wraps an observed event along with its associated topic, making it easier to inspect what events
    have passed through the system during tests.
    """

    event: BaseEvent
    topic: Topic


class AgentTestRunner(AgentRunner):
    """
    A specialized runner intended for testing agents. It extends `AgentRunner` by:
    - Observing events published by the agent and storing them for assertions in tests.
    - Providing a `test_run` context manager that sets up a test environment, including
      event subscriptions and automatic cleanup after a delay.
    - Utilities to quickly check if certain event classes (Start/Stop/Exception) have been emitted,
      and to retrieve all events of a particular type.
    """

    def __init__(
        self,
        agent_type: type[Agent],
        default_agent_config: AgentConfig,
        locale_paths: list[str] | None = None,
    ):
        super().__init__(
            servers=[NatsSettings().ENDPOINT],
            redis_url=RedisSettings().URL,
            agent_type=agent_type,
            default_agent_config=default_agent_config,
            locale_paths=locale_paths,
        )
        self.topic_manager = AgentInstanceTopicManager(
            agent_class=self.agent_class, agent_id=default_agent_config.agent_id
        )
        self.test_event_subscriber: JSSubscriber | None = None
        self.observed_events: list[ObservedEvent] = []
        self.topic: PartialAgentTopic | None = None

        self.observe_discovery_event_subscriber: AgentNCSubscriber | None = None
        self.observe_discovery_response_event_subscriber: AgentNCSubscriber | None = None

    async def send_event(
        self,
        start_event: StartEvent,
        thread_id: str,
        display_id: str,
        run_id: str,
    ):
        """
        Sends an initial event (like a StartEvent) to initiate a run.
        This allows external code to trigger a new run by injecting a start event.
        """
        publisher = JSPublisher(f"{self.agent_class}TestRunner", self.js)
        thread_topic_manager = AgentThreadTopicManager.from_agent_instance_topic_manager(
            self.topic_manager,
            thread_id,
            display_id,
            run_id,
        )
        subject = thread_topic_manager.get_subject_for_control_event_in_thread(
            start_event.event_name, event_id=start_event.event_id
        )
        await publisher.publish_event(start_event, subject)

    async def send_event_from_topic(self, start_event: StartEvent, topic: PartialAgentTopic):
        """
        Sends a StartEvent (or another initiating event) to the run identified by the PartialAgentTopic.
        This allows tests to inject their own events to drive the agent workflow.
        """
        await self.send_event(start_event, topic.thread_id, topic.display_id, topic.run_id)

    async def observe_event(self, event: BaseEvent, topic: Topic):
        """
        Handler for observed events. Whenever an event is published to the run’s thread,
        this handler stores it in self.observed_events.
        """
        self.observed_events.append(ObservedEvent(event=event, topic=topic))

    @asynccontextmanager
    async def test_run(
        self, delay_before_stop: int = 1, thread_id: str | None = None
    ) -> AsyncGenerator[PartialAgentTopic]:
        """
        A context manager that:
        1. Starts the agent runner.
        2. Sets up a subscription to observe all events for a newly generated run/thread/display IDs.
        3. Yields a PartialAgentTopic that identifies the run's context for sending events.
        4. After the context block ends, waits for a StopEvent or until `delay_before_stop` timeout is reached.

        This is useful for integration tests where you:
        - Need a clean environment (fresh thread/run).
        - Want to observe all events produced during the test scenario.
        - Want automatic teardown after tests complete.

        The `delay_before_stop` parameter acts as a maximum timeout, but the method will exit early
        if a StopEvent is detected, significantly speeding up tests that complete quickly.
        """
        yield await self.test_run_start(thread_id)
        # After leaving the context, wait for StopEvent or timeout
        # Poll every 1s to detect StopEvent early and avoid unnecessary waiting
        interval = 1
        grace_period = 1  # Grace period after StopEvent to allow async operations to complete
        max_attempts = int(delay_before_stop / interval)
        attempts = 0

        while not self.has_stop_event and attempts < max_attempts:
            await sleep(interval)
            attempts += 1

        # If StopEvent was detected, add a grace period for pending async operations
        # (e.g., ThreadContext persistence to Redis) to complete
        if self.has_stop_event:
            await sleep(grace_period)

        await self.test_run_stop()

    async def test_run_start(self, thread_id: str | None = None) -> PartialAgentTopic:
        await self.start()
        if thread_id is None:
            thread_id = str(ObjectId())
        display_id = str(ObjectId())
        run_id = str(ObjectId())

        self.test_event_subscriber = AgentNCSubscriber.for_all_thread_events(
            nc=self.nc,
            topic_manager=AgentThreadTopicManager.from_agent_instance_topic_manager(
                self.topic_manager,
                thread_id=thread_id,
                display_id=display_id,
                run_id=run_id,
            ),
            handler=self.observe_event,
            subscriber_name=f"{self.agent_class}TestRunnerEventLog",
        )
        await self.test_event_subscriber.start()

        self.observe_discovery_event_subscriber = AgentNCSubscriber.for_agent_class_discovery_request_events(
            nc=self.nc,
            topic_manager=AgentTopicManager(),
            handler=self.observe_event,
            subscriber_name="AgentTestRunnerDiscoveryRequestEventLog",
        )
        await self.observe_discovery_event_subscriber.start()

        self.observe_discovery_response_event_subscriber = AgentNCSubscriber.for_agent_class_discovery_response_events(
            nc=self.nc,
            topic_manager=AgentTopicManager(),
            handler=self.observe_event,
            subscriber_name="AgentTestRunnerDiscoveryResponseEventLog",
        )
        await self.observe_discovery_response_event_subscriber.start()

        self.topic = PartialAgentTopic(
            agent_class=self.agent_class,
            agent_id=self.default_agent_config.agent_id,
            run_id=run_id,
            thread_id=thread_id,
            display_id=display_id,
        )
        return self.topic

    async def test_run_stop(self):
        await self.test_event_subscriber.stop()
        await self.observe_discovery_event_subscriber.stop()
        await self.stop()

    async def ensure_dependent_agent_stream(self, agent_class: str) -> None:
        """
        Ensure the JetStream stream exists for a dependent agent that will be delegated to.

        Use this in tests when an agent delegates to another agent via agent-in-the-loop,
        but the delegated agent's runner is not started. This creates the stream so the
        delegation publish can succeed.
        """
        if not self.js:
            raise RuntimeError("Runner must be started before ensuring dependent agent streams")

        topic_manager = AgentClassTopicManager(agent_class=agent_class)
        stream_name, stream_subject = topic_manager.get_stream()
        stream_manager = StreamManager(self.js, stream_name, stream_subject)
        await stream_manager.ensure_stream_exists()

    @property
    def has_start_event(self) -> bool:
        """Check if a StartEvent was observed."""
        return any(isinstance(event.event, StartEvent) for event in self.observed_events)

    def get_start_event(self) -> StartEvent:
        """
        Returns the first observed StartEvent.
        Raises StopIteration if no StartEvent was observed.
        """
        return next(event.event for event in self.observed_events if isinstance(event.event, StartEvent))

    @property
    def has_stop_event(self) -> bool:
        """Check if a StopEvent was observed."""
        return any(isinstance(event.event, StopEvent) for event in self.observed_events)

    @property
    def has_exception_event(self) -> bool:
        """Check if an ExceptionEvent was observed."""
        return any(isinstance(event.event, ExceptionEvent) for event in self.observed_events)

    @property
    def has_discovery_request_event(self) -> bool:
        """Check if a DiscoveryRequestEvent was observed."""
        return any(isinstance(event.event, ClassDiscoveryRequestEvent) for event in self.observed_events)

    @property
    def has_own_agent_discovery_response_event(self) -> bool:
        """Check if an AgentDiscoveryResponseEvent with the agent's class was observed."""
        return any(
            isinstance(event.event, AgentClassDiscoveryResponseEvent) and event.event.agent_class == self.agent_class
            for event in self.observed_events
        )

    def get_topics(
        self,
        event_class: type[BaseEvent],
        exact: Annotated[bool, "Must the event be an exact match or is subclass okay?"] = False,
    ) -> list[AgentInstanceTopic]:
        """Returns the topics of all observed events of the specified class, if any are AgentTopic."""
        return [
            ev.topic
            for ev in self.observed_events
            if isinstance(ev.event, event_class)
            and (not exact or event_class.event_name_from_class() == ev.event.event_name)
            and isinstance(ev.topic, AgentInstanceTopic)
        ]

    def get_events_of_class(
        self,
        event_class: type[BaseEvent],
        exact: Annotated[bool, "Must the event be an exact match or is subclass okay?"] = False,
    ) -> list[BaseEvent]:
        """Returns all observed events of the specified class."""
        return [
            ev.event
            for ev in self.observed_events
            if isinstance(ev.event, event_class)
            and (not exact or event_class.event_name_from_class() == ev.event.event_name)
        ]

    def has_event_of_class(
        self,
        event_class: type[BaseEvent],
        exact: Annotated[bool, "Must the event be an exact match or is subclass okay?"] = False,
    ) -> bool:
        """Check if any event of the specified class was observed."""
        return len(self.get_events_of_class(event_class, exact)) > 0

    def get_event_of_class(
        self,
        event_class: type[BaseEvent],
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
        event_class: type[BaseEvent],
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
