import asyncio
import logging
from typing import Type, List, Optional

from nats.aio.client import Client as NATS
from nats.js import JetStreamContext

from agents_core.agents.abstract.Agent import Agent
from lib_core.generative_ai.agent.AgentConfig import AgentConfig
from agents_core.dispatchers.Dispatcher import Dispatcher
from agents_core.i18n.AgentLocaleHandler import AgentLocaleHandler
from lib_core.nats.events import StartEvent
from lib_core.nats.events.discovery.DiscoveryRequestEvent import DiscoveryRequestEvent
from lib_core.nats.events.discovery.AgentDiscoveryResponseEvent import AgentDiscoveryResponseEvent, StartEventSpecs
from lib_core.nats.publishers.JSPublisher import JSPublisher
from lib_core.nats.publishers.NCPublisher import NCPublisher
from lib_core.nats.subscribers.JSSubscriber import JSSubscriber
from lib_core.nats.subscribers.NCSubscriber import NCSubscriber
from lib_core.nats.topic_managers.TopicManager import TopicManager
from lib_core.nats.topic_managers.agents.AgentInstanceTopicManager import AgentInstanceTopicManager
from lib_core.nats.topic_managers.agents.AgentThreadTopicManager import AgentThreadTopicManager
from lib_core.nats.topics import DiscoveryTopic

logger = logging.getLogger(__name__)

class AgentRunner:
    def __init__(self, servers: List[str], agent_type: Type[Agent], agent_config: AgentConfig, locale_paths: Optional[List[str]]=None):
        self.servers = servers
        self.agent_type = agent_type
        self.agent_config = agent_config
        self.running = False
        self._stop_event = asyncio.Event()

        self.agent_class = self.agent_type.__name__
        self.topic_manager = AgentInstanceTopicManager(self.agent_class, self.agent_config.agent_id)

        self.nc: NATS | None = None
        self.js: JetStreamContext | None = None

        self.dispatcher: Dispatcher | None = None

        self.discovery_event_subscriber: NCSubscriber[DiscoveryRequestEvent] | None = None
        self.control_event_subscriber: JSSubscriber | None = None

        self.nc_publisher: NCPublisher[AgentDiscoveryResponseEvent] | None = None

        self.locale_handler = AgentLocaleHandler(locale_paths)

    async def discovery_handler(self, event: DiscoveryRequestEvent, topic: DiscoveryTopic):

        if topic.agent_class not in [self.agent_class, "*"] or topic.agent_id not in [self.agent_config.agent_id, "*"]:
            logger.debug(f"Discovery request for {topic.agent_class} with id {topic.agent_id} does not match this agent.")
            return

        logger.debug(f"Received discovery request for {topic.agent_class} with id {topic.agent_id}.")
        subject = self.topic_manager.get_agent_discovery_subject_response(topic.call_id)
        start_events = [
            StartEventSpecs(event_type=event.__name__, event_schema=event.model_json_schema())
            for event in self.agent_type.get_start_events()
        ]
        agent_discovery_response_event = AgentDiscoveryResponseEvent(
            agent_class=self.agent_class,
            agent_id=self.agent_config.agent_id,
            agent_config=self.agent_config,
            start_events=start_events,
        )
        await self.nc_publisher.publish_event(agent_discovery_response_event, subject)

    async def start(self):
        if self.running:
            logger.warning("AgentRunner is already running.")
            return

        self.running = True
        self._stop_event.clear()

        self.nc = NATS()
        await self.nc.connect(servers=self.servers) # ["nats://localhost:4222"]

        self.js = self.nc.jetstream()

        # Initialize dispatcher
        self.dispatcher = Dispatcher(self.agent_type, self.agent_config, self.nc, self.js, self.topic_manager, self.locale_handler)

        self.nc_publisher = NCPublisher(self.nc)
        self.discovery_event_subscriber = NCSubscriber.for_agent_discovery_request_events(self.nc, TopicManager(), self.discovery_handler)
        await self.discovery_event_subscriber.start()

        # Start js subscriber
        self.control_event_subscriber = JSSubscriber.for_agent_instance_control_events(
            self.nc,
            self.topic_manager,
            js=self.js,
            handler=self.dispatcher.handle_event,
        )
        await self.control_event_subscriber.start()

        logger.debug(f"{self.agent_class} is now running and subscribed to incoming messages.")
        asyncio.create_task(self._run_loop())

    async def stop(self):
        if not self.running:
            logger.warning("AgentRunner is not running.")
            return

        logger.debug(f"Shutting down {self.agent_class}...")
        self._stop_event.set()
        self.running = False
        await self.nc.close()

    async def _run_loop(self):
        try:
            while not self._stop_event.is_set():
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            await self.nc.close()

    async def run_forever(self):
        """Convenience method to start and run indefinitely, waiting for manual stop."""
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
        publisher = JSPublisher(self.js)
        thread_topic_manager = AgentThreadTopicManager.from_agent_instance_topic_manager(
            self.topic_manager,
            thread_id,
            display_id,
            run_id,
        )
        subject = thread_topic_manager.get_subject_for_control_event_in_thread(start_event.__class__.__name__, event_id=start_event.event_id)
        await publisher.publish_event(start_event, subject)


