import asyncio
import logging
from typing import List, Optional, Type

from aihub_lib.nats.events import StartEvent, UserMessageEvent
from aihub_lib.nats.events.discovery.agent.AgentDiscoveryResponseEvent import AgentDiscoveryResponseEvent, EventSpecs
from aihub_lib.nats.events.discovery.DiscoveryRequestEvent import DiscoveryRequestEvent
from aihub_lib.nats.events.discovery.process.ProcessDiscoveryResponseEvent import ProcessDiscoveryResponseEvent
from aihub_lib.nats.publishers.JSPublisher import JSPublisher
from aihub_lib.nats.publishers.NCPublisher import NCPublisher
from aihub_lib.nats.subscribers.JSSubscriber import JSSubscriber
from aihub_lib.nats.subscribers.NCSubscriber import NCSubscriber
from aihub_lib.nats.topic_managers.agents.AgentThreadTopicManager import AgentThreadTopicManager
from aihub_lib.nats.topic_managers.agents.AgentTopicManager import AgentTopicManager
from aihub_lib.nats.topic_managers.process.ProcessInstanceTopicManager import ProcessInstanceTopicManager
from aihub_lib.nats.topic_managers.process.ProcessTopicManager import ProcessTopicManager
from aihub_lib.nats.topics import DiscoveryTopic, ProcessDiscoveryTopic
from aihub_lib.nats.workflow.visualizers.WorkflowVisualizer import WorkflowVisualizer
from nats.aio.client import Client as NATS
from nats.js import JetStreamContext
from redis.asyncio import ConnectionPool, Redis

from aihub_process.agentic_processes.AgenticProcess import AgenticProcess
from aihub_process.dispatchers.ProcessDispatcher import ProcessDispatcher
from aihub_process.i18n.ProcessLocaleHandler import ProcessLocaleHandler

logger = logging.getLogger(__name__)


class ProcessRunner:

    def __init__(
        self,
        servers: List[str],
        redis_url: str,
        process_type: Type[AgenticProcess],
        process_id: str,
        locale_paths: Optional[List[str]] = None,
    ):
        if not isinstance(process_type, type):
            raise ValueError("process_type must be a class, not an instance or module.")
        if not issubclass(process_type, AgenticProcess):
            raise ValueError("process_type must be a subclass of AgenticProcess.")

        self.servers = servers
        self.redis_url = redis_url
        self.process_type = process_type
        self.process_id = process_id

        self.running = False
        self._stop_signal = asyncio.Event()

        self.process_class = self.process_type.__name__
        self.topic_manager = ProcessInstanceTopicManager(self.process_class, self.process_id)

        self.nc: Optional[NATS] = None
        self.js: Optional[JetStreamContext] = None

        self.dispatcher: Optional[ProcessDispatcher] = None

        self.discovery_event_subscriber: Optional[NCSubscriber[DiscoveryRequestEvent]] = None
        self.control_event_subscriber: Optional[JSSubscriber] = None
        self.nc_publisher: Optional[NCPublisher[ProcessDiscoveryResponseEvent]] = None

        self.locale_handler = ProcessLocaleHandler(locale_paths=locale_paths)

    async def discovery_handler(self, event: DiscoveryRequestEvent, topic: ProcessDiscoveryTopic):
        """
        Handles discovery requests by returning an `ProcessDiscoveryResponseEvent`.

        If the discovery request doesn't match this agent (i.e., different process_class/process_id), it ignores it.
        """
        if topic.process_class not in [self.process_class, "*"] or topic.process_id not in [self.process_id, "*"]:
            logger.debug(
                f"Discovery request for {topic.process_class} with id {topic.process_id} does not match this process."
            )
            return

        logger.debug(f"Received discovery request for {topic.process_class} with id {topic.process_id}.")
        subject = self.topic_manager.get_process_discovery_subject_response(topic.call_id)

        process_discovery_response_event = ProcessDiscoveryResponseEvent(
            process_class=self.process_class,
            process_id=self.process_id,
        )
        await self.nc_publisher.publish_event(process_discovery_response_event, subject)

    async def start(self):
        """
        Connects to NATS, sets up JetStream, initializes the AgentDispatcher and subscribers,
        and starts listening for events.

        - Starts the discovery subscriber so other services can discover this process' capabilities.
        - Starts the control event subscriber to handle workflow execution.
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

        # Initialize dispatcher
        self.dispatcher = ProcessDispatcher(
            self.process_type,
            self.nc,
            self.js,
            self.redis,
            self.topic_manager,
            self.locale_handler,
        )
        await self.dispatcher.start()

        self.nc_publisher = NCPublisher(self.nc)
        self.discovery_event_subscriber = NCSubscriber.for_process_discovery_request_events( # TODO
            self.nc, ProcessTopicManager(), self.discovery_handler
        )
        await self.discovery_event_subscriber.start()

        # Subscribe to control events
        self.control_event_subscriber = JSSubscriber.for_process_instance_control_events(  # TODO
            self.nc,
            self.topic_manager,
            handler=self.dispatcher.handle_event,
            js=self.js,
            queue_group=f"process_runner_{self.process_class}_{self.process_id}",
        )
        await self.control_event_subscriber.start()

        logger.debug(f"{self.process_class} is now running and subscribed to incoming messages.")
        asyncio.create_task(self._run_loop())

    async def stop(self):
        """
        Stops the process by setting a stop event, unsubscribing, and closing the NATS connection.
        """
        if not self.running:
            logger.warning("AgentRunner is not running.")
            return

        logger.debug(f"Shutting down {self.process_class}...")
        self._stop_signal.set()
        self.running = False

        await self.control_event_subscriber.stop()
        await self.dispatcher.stop()

        if self.nc:
            await self.nc.close()

        if self.redis:
            await self.redis.close()

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
        Starts the process and waits indefinitely (or until a stop event is triggered).
        Useful for production usage where the process should run until manually stopped.
        """
        logger.debug(f"Starting {self.process_class}.{self.process_id}")
        await self.start()
        try:
            await self._stop_signal.wait()
        except KeyboardInterrupt:
            await self.stop()
