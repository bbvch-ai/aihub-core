import asyncio
import logging
from typing import Type, List

from nats.aio.client import Client as NATS
from nats.js import JetStreamContext

from agents_core.agents.abstract.Agent import Agent
from agents_core.agents.abstract.AgentConfig import AgentConfig
from agents_core.dispatchers.Dispatcher import Dispatcher
from lib_core.nats.events import StartEvent
from lib_core.nats.publishers.JSPublisher import JSPublisher
from lib_core.nats.subscribers.JSSubscriber import JSSubscriber
from lib_core.nats.topic_managers.agents.AgentInstanceTopicManager import AgentInstanceTopicManager
from lib_core.nats.topic_managers.agents.AgentThreadTopicManager import AgentThreadTopicManager

logger = logging.getLogger(__name__)

class AgentRunner:
    def __init__(self, servers: List[str], agent_class: Type[Agent], agent_config: AgentConfig):
        self.servers = servers
        self.agent_class = agent_class
        self.agent_config = agent_config
        self.running = False
        self._stop_event = asyncio.Event()

        self.agent_name = self.agent_class.__name__
        self.topic_manager = AgentInstanceTopicManager(self.agent_name, self.agent_config.agent_id)

        self.nc: NATS | None = None
        self.js: JetStreamContext | None = None

        self.dispatcher: Dispatcher | None = None
        self.subscriber: JSSubscriber | None = None

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
        self.dispatcher = Dispatcher(self.agent_class, self.agent_config, self.nc, self.js, self.topic_manager)

        # Start subscriber
        self.subscriber = JSSubscriber.for_agent_instance_control_events(
            self.nc,
            self.topic_manager,
            js=self.js,
            handler=self.dispatcher.handle_event,
        )
        await self.subscriber.start()

        logger.debug(f"{self.agent_name} is now running and subscribed to incoming messages.")
        asyncio.create_task(self._run_loop())

    async def stop(self):
        if not self.running:
            logger.warning("AgentRunner is not running.")
            return

        logger.debug(f"Shutting down {self.agent_name}...")
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


