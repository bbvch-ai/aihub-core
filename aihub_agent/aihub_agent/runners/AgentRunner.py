import asyncio
import logging
from typing import List, Optional, Type

from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.nats.events import StartEvent, UserMessageEvent
from aihub_lib.nats.events.discovery.AgentDiscoveryResponseEvent import AgentDiscoveryResponseEvent, EventSpecs
from aihub_lib.nats.events.discovery.DiscoveryRequestEvent import DiscoveryRequestEvent
from aihub_lib.nats.publishers.JSPublisher import JSPublisher
from aihub_lib.nats.publishers.NCPublisher import NCPublisher
from aihub_lib.nats.subscribers.JSSubscriber import JSSubscriber
from aihub_lib.nats.subscribers.NCSubscriber import NCSubscriber
from aihub_lib.nats.topic_managers.agents.AgentInstanceTopicManager import AgentInstanceTopicManager
from aihub_lib.nats.topic_managers.agents.AgentThreadTopicManager import AgentThreadTopicManager
from aihub_lib.nats.topic_managers.TopicManager import TopicManager
from aihub_lib.nats.topics import DiscoveryTopic
from nats.aio.client import Client as NATS
from nats.js import JetStreamContext
from redis.asyncio import ConnectionPool, Redis

from aihub_agent.agents.abstract.Agent import Agent
from aihub_agent.dispatchers.Dispatcher import Dispatcher
from aihub_agent.i18n.AgentLocaleHandler import AgentLocaleHandler

logger = logging.getLogger(__name__)


class AgentRunner:
    """
    Manages the lifecycle of an agent, connecting it to NATS/JetStream, subscribing to event streams,
    and orchestrating the dispatch of events to the agent's steps via the Dispatcher.

    ### Why AgentRunner?
    In complex AI workflows, agents:
    - Receive events (like StartEvent) from distributed sources.
    - Respond to discovery requests (to expose their capabilities).
    - Handle incoming ControlEvents that trigger steps.

    The AgentRunner brings these elements together. It:
    - Connects to NATS and JetStream.
    - Sets up subscriptions for discovery and control events.
    - Hooks into the Dispatcher to execute steps in response to events.
    - Provides methods to start/stop the agent and send initial events (like StartEvent).

    By encapsulating these concerns, AgentRunner simplifies the startup and operation of an agent in
    a distributed environment.

    ### Key Responsibilities
    - **Discovery Handling:**
      On receiving a `DiscoveryRequestEvent`, responds with an `AgentDiscoveryResponseEvent` describing
      the agent’s start events and configuration.
    - **Control Event Handling:**
      Subscribes to control events and delegates them to the Dispatcher for step execution.
    - **Lifecycle Management:**
      Provides `start()`, `stop()`, and `run_forever()` methods to manage the agent’s runtime.
    - **Sending Initial Events:**
      `send_event()` can send a `StartEvent` or other events to kick off a run.

    ### Example
    ```python
    runner = AgentRunner(servers=[NatsConfig().NATS_ENDPOINT], agent_type=MyAgent, agent_config=my_config)
    await runner.run_forever()
    ```
    This code connects to NATS, listens for events, and processes them indefinitely until stopped.
    """

    def __init__(
        self,
        servers: List[str],
        redis_url: str,
        agent_type: Type[Agent],
        agent_config: AgentConfig,
        locale_paths: Optional[List[str]] = None,
    ):
        self.servers = servers
        self.redis_url = redis_url
        self.agent_type = agent_type
        self.agent_config = agent_config
        self.running = False
        self._stop_event = asyncio.Event()

        self.agent_class = self.agent_type.__name__
        self.topic_manager = AgentInstanceTopicManager(self.agent_class, self.agent_config.agent_id)

        self.nc: Optional[NATS] = None
        self.js: Optional[JetStreamContext] = None

        self.dispatcher: Optional[Dispatcher] = None

        self.discovery_event_subscriber: Optional[NCSubscriber[DiscoveryRequestEvent]] = None
        self.control_event_subscriber: Optional[JSSubscriber] = None
        self.nc_publisher: Optional[NCPublisher[AgentDiscoveryResponseEvent]] = None

        self.locale_handler = AgentLocaleHandler(locale_paths=locale_paths)

    async def discovery_handler(self, event: DiscoveryRequestEvent, topic: DiscoveryTopic):
        """
        Handles discovery requests by returning an `AgentDiscoveryResponseEvent` that includes:
        - Agent class, ID
        - Agent configuration
        - Specs for start events (the events that can initiate a run)

        If the discovery request doesn't match this agent (i.e., different agent_class/agent_id), it ignores it.
        """
        if topic.agent_class not in [self.agent_class, "*"] or topic.agent_id not in [
            self.agent_config.agent_id,
            "*",
        ]:
            logger.debug(
                f"Discovery request for {topic.agent_class} with id {topic.agent_id} does not match this agent."
            )
            return

        logger.debug(f"Received discovery request for {topic.agent_class} with id {topic.agent_id}.")
        subject = self.topic_manager.get_agent_discovery_subject_response(topic.call_id)

        start_events = self.agent_type.get_start_events()
        start_event_specs = [
            EventSpecs(event_type=e.__name__, event_schema=e.model_json_schema()) for e in start_events
        ]

        stop_events = self.agent_type.get_stop_events()
        stop_event_specs = [EventSpecs(event_type=e.__name__, event_schema=e.model_json_schema()) for e in stop_events]
        agent_discovery_response_event = AgentDiscoveryResponseEvent(
            agent_class=self.agent_class,
            agent_id=self.agent_config.agent_id,
            is_conversational=any([issubclass(event, UserMessageEvent) for event in start_events]),
            agent_config=self.agent_config,
            start_events=start_event_specs,
            stop_events=stop_event_specs,
        )
        await self.nc_publisher.publish_event(agent_discovery_response_event, subject)

    async def start(self):
        """
        Connects to NATS, sets up JetStream, initializes the Dispatcher and subscribers,
        and starts listening for events.

        - Starts the discovery subscriber so other services can discover this agent's capabilities.
        - Starts the control event subscriber to handle workflow execution.
        """
        if self.running:
            logger.warning("AgentRunner is already running.")
            return

        self.running = True
        self._stop_event.clear()

        self.nc = NATS()
        await self.nc.connect(servers=self.servers)

        self.js = self.nc.jetstream(timeout=60, publish_async_max_pending=10_000)
        _, host, port = self.redis_url.split(":")
        self.redis = Redis(connection_pool=ConnectionPool(host=host[2:], port=port))

        # Initialize dispatcher
        self.dispatcher = Dispatcher(
            self.agent_type,
            self.agent_config,
            self.nc,
            self.js,
            self.redis,
            self.topic_manager,
            self.locale_handler,
        )

        self.nc_publisher = NCPublisher(self.nc)
        self.discovery_event_subscriber = NCSubscriber.for_agent_discovery_request_events(
            self.nc, TopicManager(), self.discovery_handler
        )
        await self.discovery_event_subscriber.start()

        # Subscribe to control events
        self.control_event_subscriber = JSSubscriber.for_agent_instance_control_events(
            self.nc,
            self.topic_manager,
            handler=self.dispatcher.handle_event,
            js=self.js,
        )
        await self.control_event_subscriber.start()

        logger.debug(f"{self.agent_class} is now running and subscribed to incoming messages.")
        asyncio.create_task(self._run_loop())

    async def stop(self):
        """
        Stops the agent by setting a stop event, unsubscribing, and closing the NATS connection.
        """
        if not self.running:
            logger.warning("AgentRunner is not running.")
            return

        logger.debug(f"Shutting down {self.agent_class}...")
        self._stop_event.set()
        self.running = False

        if self.nc:
            await self.nc.drain()
            await self.nc.close()

        if self.redis:
            await self.redis.close()

    async def _run_loop(self):
        """A background task that keeps the runner alive until stopped."""
        try:
            while not self._stop_event.is_set():
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            if self.nc:
                await self.nc.close()

    async def run_forever(self):
        """
        Starts the agent and waits indefinitely (or until a stop event is triggered).
        Useful for production usage where the agent should run until manually stopped.
        """
        logger.debug(f"Starting {self.agent_class}.{self.agent_config.agent_id}")
        await self.start()
        try:
            await self._stop_event.wait()
        except KeyboardInterrupt:
            await self.stop()

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
        publisher = JSPublisher(self.js)
        thread_topic_manager = AgentThreadTopicManager.from_agent_instance_topic_manager(
            self.topic_manager,
            thread_id,
            display_id,
            run_id,
        )
        subject = thread_topic_manager.get_subject_for_control_event_in_thread(
            start_event.__class__.__name__, event_id=start_event.event_id
        )
        await publisher.publish_event(start_event, subject)
