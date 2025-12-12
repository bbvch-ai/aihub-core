import asyncio
import logging

from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.infrastructure.api.AIHubSettings import AIHubSettings
from aihub_lib.infrastructure.mongo.MongoSettings import MongoSettings
from aihub_lib.nats.events import UserMessageEvent
from aihub_lib.nats.events.discovery.agent.AgentClassDiscoveryResponseEvent import (
    AgentClassDiscoveryResponseEvent,
    AgentConfigSpecs,
)
from aihub_lib.nats.events.discovery.ClassDiscoveryRequestEvent import ClassDiscoveryRequestEvent
from aihub_lib.nats.events.discovery.EventSpecs import EventSpecs
from aihub_lib.nats.events.form.base.FormkitElement import FormkitElement
from aihub_lib.nats.publishers.NCPublisher import NCPublisher
from aihub_lib.nats.subscribers.agent.AgentJSSubscriber import AgentJSSubscriber
from aihub_lib.nats.subscribers.agent.AgentNCSubscriber import AgentNCSubscriber
from aihub_lib.nats.subscribers.JSSubscriber import JSSubscriber
from aihub_lib.nats.subscribers.NCSubscriber import NCSubscriber
from aihub_lib.nats.topic_managers.agents.AgentClassTopicManager import AgentClassTopicManager
from aihub_lib.nats.topic_managers.agents.AgentTopicManager import AgentTopicManager
from aihub_lib.nats.topics.discovery.agent.AgentClassDiscoveryTopic import AgentClassDiscoveryTopic
from aihub_lib.nats.workflow.visualizers.WorkflowVisualizer import WorkflowVisualizer
from mongoengine import connect, disconnect
from mongoengine.connection import get_connection
from nats.aio.client import Client as NATS
from nats.js import JetStreamContext
from redis.asyncio import ConnectionPool, Redis

from aihub_agent.agents.Agent import Agent
from aihub_agent.dispatchers.AgentDispatcher import AgentDispatcher
from aihub_agent.i18n.AgentLocaleHandler import AgentLocaleHandler

logger = logging.getLogger(__name__)


class AgentRunner:
    """
    An agent runner is responsible for connecting with external services like NATs, JetStream, and Redis, as well
    as running the agent through an agent dispatcher.
    The runner is also responsible for making the agent discoverable by responding to discovery requests.
    """

    def __init__(
        self,
        servers: list[str],
        redis_url: str,
        agent_type: type[Agent],
        default_agent_config: AgentConfig,
        locale_paths: list[str] | None = None,
        form: list[FormkitElement] | None = None,
    ):
        if not isinstance(agent_type, type):
            raise ValueError("agent_type must be a class, not an instance or module.")
        if not issubclass(agent_type, Agent):
            raise ValueError("agent_type must be a subclass of Agent.")

        self.servers = servers
        self.redis_url = redis_url
        self.agent_type = agent_type
        self.default_agent_config = default_agent_config
        self.agent_config_type = default_agent_config.__class__
        self.form = form or []

        self.running = False
        self._stop_signal = asyncio.Event()
        self._loop_task: asyncio.Task | None = None

        self.agent_class = self.agent_type.__name__
        self.topic_manager = AgentClassTopicManager(agent_class=self.agent_class)

        self.nc: NATS | None = None
        self.js: JetStreamContext | None = None

        self.dispatcher: AgentDispatcher | None = None

        self.discovery_event_subscriber: NCSubscriber[ClassDiscoveryRequestEvent] | None = None
        self.control_event_subscriber: JSSubscriber | None = None
        self.nc_publisher: NCPublisher[AgentClassDiscoveryResponseEvent] | None = None

        self.locale_handler = AgentLocaleHandler(locale_paths=locale_paths)

    async def discovery_handler(self, event: ClassDiscoveryRequestEvent, topic: AgentClassDiscoveryTopic):
        """
        Responds to discovery requests by publishing an AgentDiscoveryResponseEvent that includes the basic
        agent configuration as well as some carefully crafted event specifications.
        """
        if topic.agent_class not in [self.agent_class, "*"]:
            logger.debug(f"Discovery request for {topic.agent_class} does not match this agent.")
            return

        logger.debug(f"Received discovery request for {topic.agent_class}.")
        subject = self.topic_manager.get_agent_class_discovery_subject_response(
            topic.call_id, agent_class=self.agent_class
        )

        start_events = self.agent_type.get_start_events()
        start_event_specs = [EventSpecs.from_event_class(e) for e in start_events]

        stop_events = self.agent_type.get_stop_events()
        stop_event_specs = [EventSpecs.from_event_class(e) for e in stop_events]

        hitl_request_events = self.agent_type.get_hitl_request_events()
        hitl_request_event_specs = [EventSpecs.from_event_class(e) for e in hitl_request_events]

        hitl_response_events = self.agent_type.get_hitl_response_events()
        hitl_response_event_specs = [EventSpecs.from_event_class(e) for e in hitl_response_events]

        network_graph = WorkflowVisualizer(agent=self.agent_type)
        network_graph.build_workflow_graph()

        agent_config_specs = AgentConfigSpecs.from_agent_config(self.default_agent_config, form=self.form)

        agent_discovery_response_event = AgentClassDiscoveryResponseEvent(
            agent_class=self.agent_class,
            agent_config_specs=agent_config_specs,
            is_conversational=any([issubclass(event, UserMessageEvent) for event in start_events]),
            start_events=start_event_specs,
            stop_events=stop_event_specs,
            hitl_request_events=hitl_request_event_specs,
            hitl_response_events=hitl_response_event_specs,
            network_graph=network_graph.to_pydantic(),
            default_agent_config=self.default_agent_config,
        )
        await self.nc_publisher.publish_event(agent_discovery_response_event, subject)

    async def start(self):
        """
        Connects to all external services and starts the agent dispatcher with connecting it to a JetStream stream.
        """
        if self.running:
            logger.warning("AgentRunner is already running.")
            return

        self.running = True
        self._stop_signal.clear()

        self.nc = NATS()
        await self.nc.connect(servers=self.servers)

        self.js = self.nc.jetstream(timeout=60, publish_async_max_pending=10_000)
        _, host, port = self.redis_url.split(":")
        self.redis = Redis(connection_pool=ConnectionPool(host=host[2:], port=port))

        # Connect to MongoDB (skip if already connected)
        try:
            get_connection()
        except Exception:
            connect(
                db=AIHubSettings().MONGO_MAIN_DB_NAME,
                host=MongoSettings().CONNECTION_STRING.get_secret_value(),
                uuidRepresentation="standard",
            )

        # Initialize dispatcher
        self.dispatcher = AgentDispatcher(
            self.agent_type,
            self.default_agent_config,
            self.nc,
            self.js,
            self.redis,
            self.topic_manager,
            self.locale_handler,
        )
        await self.dispatcher.start()

        self.nc_publisher = NCPublisher(f"{self.agent_class}RunnerDiscoveryResponse", self.nc)
        self.discovery_event_subscriber = AgentNCSubscriber.for_agent_class_discovery_request_events(
            self.nc,
            AgentTopicManager(),
            self.discovery_handler,
            subscriber_name=f"{self.agent_class}RunnerDiscoveryRequest",
        )
        await self.discovery_event_subscriber.start()

        # Subscribe to control events
        self.control_event_subscriber = AgentJSSubscriber.for_agent_class_control_events(
            self.nc,
            self.topic_manager,
            handler=self.dispatcher.handle_event,
            js=self.js,
            queue_group=f"agent_runner_{self.agent_class}",
            subscriber_name=f"{self.agent_class}RunnerControlEvents",
        )
        await self.control_event_subscriber.start()

        logger.debug(f"{self.agent_class} is now running and subscribed to incoming messages.")
        self._loop_task = asyncio.create_task(self._run_loop())

    async def stop(self):
        """
        Stops the agent by setting a stop event, unsubscribing, and closing the NATS connection.
        """
        if not self.running:
            logger.warning("AgentRunner is not running.")
            return

        logger.debug(f"Shutting down {self.agent_class}...")
        self._stop_signal.set()

        if self._loop_task is not None:
            await self._loop_task

        else:
            logger.exception(f"Loop task was not running for {self.agent_class}.")

        self.running = False

        await self.discovery_event_subscriber.stop()
        await self.control_event_subscriber.stop()
        await self.dispatcher.stop()

        if self.nc:
            await self.nc.close()

        if self.redis:
            await self.redis.close()

        disconnect()

    async def _run_loop(self):
        """A background task that keeps the runner alive until stopped."""
        try:
            while not self._stop_signal.is_set():
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            if self.nc:
                await self.nc.close()

    async def run_forever(self):
        """
        Starts the agent and waits indefinitely (or until a stop event is triggered).
        Useful for production usage where the agent should run until manually stopped.
        """
        logger.debug(f"Starting {self.agent_class}")
        await self.start()
        try:
            await self._stop_signal.wait()
        except KeyboardInterrupt:
            await self.stop()
