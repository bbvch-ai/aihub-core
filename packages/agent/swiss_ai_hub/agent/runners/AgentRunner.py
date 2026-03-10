import asyncio
import logging

from mongoengine import connect, disconnect
from mongoengine.connection import get_connection
from nats.aio.client import Client as NATS
from nats.js import JetStreamContext
from pymilvus import MilvusClient
from redis.asyncio import Redis
from swiss_ai_hub.core.agents.AgentConfig import AgentConfig
from swiss_ai_hub.core.infrastructure.api.AIHubSettings import AIHubSettings
from swiss_ai_hub.core.infrastructure.milvus.MilvusSettings import MilvusSettings
from swiss_ai_hub.core.infrastructure.mongo.MongoSettings import MongoSettings
from swiss_ai_hub.core.infrastructure.nats.NatsSettings import NatsSettings
from swiss_ai_hub.core.infrastructure.redis.RedisSettings import RedisSettings
from swiss_ai_hub.core.nats.events.discovery.agent.AgentClassDiscoveryResponseEvent import (
    AgentClassDiscoveryResponseEvent,
    AgentConfigSpecs,
)
from swiss_ai_hub.core.nats.events.discovery.ClassDiscoveryRequestEvent import ClassDiscoveryRequestEvent
from swiss_ai_hub.core.nats.events.discovery.EventSpecs import EventSpecs
from swiss_ai_hub.core.nats.events.form.TemplateData import TemplateData
from swiss_ai_hub.core.nats.events.user.UserMessageEvent import UserMessageEvent
from swiss_ai_hub.core.nats.publishers.NCPublisher import NCPublisher
from swiss_ai_hub.core.nats.subscribers.agent.AgentJSSubscriber import AgentJSSubscriber
from swiss_ai_hub.core.nats.subscribers.agent.AgentNCSubscriber import AgentNCSubscriber
from swiss_ai_hub.core.nats.subscribers.JSSubscriber import JSSubscriber
from swiss_ai_hub.core.nats.subscribers.NCSubscriber import NCSubscriber
from swiss_ai_hub.core.nats.topic_managers.agents.AgentClassTopicManager import AgentClassTopicManager
from swiss_ai_hub.core.nats.topic_managers.agents.AgentTopicManager import AgentTopicManager
from swiss_ai_hub.core.nats.topics.discovery.agent.AgentClassDiscoveryTopic import AgentClassDiscoveryTopic
from swiss_ai_hub.core.nats.workflow.visualizers.WorkflowVisualizer import WorkflowVisualizer
from swiss_ai_hub.core.routes.health.dto.HealthResponse import AgentHealthChecks
from swiss_ai_hub.core.routes.health.health_checks import check_milvus, check_nats_sync, check_redis_sync
from swiss_ai_hub.core.routes.health.HealthServer import HealthCheckProvider, HealthServer

from swiss_ai_hub.agent.agents.Agent import Agent
from swiss_ai_hub.agent.dispatchers.AgentDispatcher import AgentDispatcher
from swiss_ai_hub.agent.i18n.AgentLocaleHandler import AgentLocaleHandler

logger = logging.getLogger(__name__)


class AgentRunner(HealthCheckProvider):
    """
    An agent runner is responsible for connecting with external services like NATs, JetStream, and Redis, as well
    as running the agent through an agent dispatcher.
    The runner is also responsible for making the agent discoverable by responding to discovery requests.

    The agent_config parameter should be a form-mode AgentConfig instance (created via as_form()).
    It contains:
    - Configurable fields: FormKit elements that define the form for UI configuration
    - Non-configurable fields: Actual values that are deployment-specific and not user-editable

    The form is automatically extracted from agent_config.to_formkit_form().
    Non-configurable values are merged with incoming StartEvent configs by the dispatcher.

    Class-level metadata (name, description, icon) is extracted from the agent_type class variables.
    """

    def __init__(
        self,
        agent_type: type[Agent],
        agent_config: AgentConfig,
        templates: list[AgentConfig] | None = None,
        locale_paths: list[str] | None = None,
        health_port: int = 8080,
    ):
        if not isinstance(agent_type, type):
            raise ValueError("agent_type must be a class, not an instance or module.")
        if not issubclass(agent_type, Agent):
            raise ValueError("agent_type must be a subclass of Agent.")

        self.agent_type = agent_type
        self.agent_config = agent_config
        self.templates = templates or []
        self.agent_config_type = agent_config.__class__

        self.name = agent_type.name
        self.description = agent_type.description
        self.icon = agent_type.icon

        self.form = agent_config.to_formkit_form()

        self.running = False
        self._stop_signal = asyncio.Event()
        self._loop_task: asyncio.Task | None = None

        self.agent_class = self.agent_type.__name__
        self.topic_manager = AgentClassTopicManager(agent_class=self.agent_class)

        self.nc: NATS | None = None
        self.js: JetStreamContext | None = None
        self.redis: Redis | None = None
        self.milvus_client: MilvusClient | None = None

        self.dispatcher: AgentDispatcher | None = None

        self.discovery_event_subscriber: NCSubscriber[ClassDiscoveryRequestEvent] | None = None
        self.control_event_subscriber: JSSubscriber | None = None
        self.nc_publisher: NCPublisher[AgentClassDiscoveryResponseEvent] | None = None

        self.locale_handler = AgentLocaleHandler(locale_paths=locale_paths)

        self._loop: asyncio.AbstractEventLoop | None = None
        self._health_server = HealthServer(
            provider=self,
            default_port=health_port,
            port_env_var="AGENT_HEALTH_PORT",
        )

    @property
    def entity_name(self) -> str:
        return self.agent_class

    @property
    def entity_type(self) -> str:
        return "agent"

    def get_readiness_checks(self) -> AgentHealthChecks:
        return AgentHealthChecks(
            running=self.running,
            nats=check_nats_sync(self.nc, self._loop) if self._loop else False,
            redis=check_redis_sync(self.redis, self._loop) if self._loop else False,
            milvus=check_milvus(self.milvus_client),
        )

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

        agent_config_specs = AgentConfigSpecs.from_agent_config(self.agent_config, self.agent_class)

        templates_data: list[TemplateData] = [t.to_template_data(self.agent_config) for t in self.templates]

        agent_discovery_response_event = AgentClassDiscoveryResponseEvent(
            agent_class=self.agent_class,
            name=self.name,
            description=self.description,
            icon=self.icon,
            form=self.form,
            agent_config_specs=agent_config_specs,
            is_conversational=any([issubclass(event, UserMessageEvent) for event in start_events]),
            start_events=start_event_specs,
            stop_events=stop_event_specs,
            hitl_request_events=hitl_request_event_specs,
            hitl_response_events=hitl_response_event_specs,
            network_graph=network_graph.to_pydantic(),
            templates=templates_data,
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
        self._loop = asyncio.get_running_loop()

        # Connect to NATs and Redis
        self.nc = await NatsSettings.create_client()
        self.js = self.nc.jetstream(timeout=60, publish_async_max_pending=10_000)
        self.redis = RedisSettings.create_client()

        # Connect to Milvus
        milvus_settings = MilvusSettings()
        self.milvus_client = MilvusClient(uri=milvus_settings.URL, token=milvus_settings.get_token())

        # Connect to MongoDB (skip if already connected)
        try:
            get_connection()
        except Exception:
            connect(
                db=AIHubSettings().MONGO_MAIN_DB_NAME,
                host=MongoSettings().CONNECTION_STRING.get_secret_value(),
                uuidRepresentation="standard",
            )

        self.dispatcher = AgentDispatcher(
            self.agent_type,
            self.agent_config,
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

        # Start health check server
        self._health_server.start()

    async def stop(self):
        """
        Stops the agent by setting a stop event, unsubscribing, and closing the NATS connection.
        """
        if not self.running:
            logger.warning("AgentRunner is not running.")
            return

        logger.debug(f"Shutting down {self.agent_class}...")

        # Stop health check server first
        self._health_server.stop()
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

        if self.milvus_client:
            self.milvus_client.close()

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
