import asyncio
import json
import logging
import os
import socket
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

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


def _check_redis(redis: Redis | None) -> bool:
    """Check if Redis connection is healthy by pinging the server."""
    if redis is None:
        return False
    try:
        # Run async ping in sync context (health handler runs in separate thread)
        return asyncio.run(redis.ping())
    except Exception:
        return False


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
        health_port: int = 8080,
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

        self.running = False
        self._stop_signal = asyncio.Event()
        self._loop_task: asyncio.Task | None = None

        self.agent_class = self.agent_type.__name__
        self.topic_manager = AgentClassTopicManager(agent_class=self.agent_class)

        self.nc: NATS | None = None
        self.js: JetStreamContext | None = None
        self.redis: Redis | None = None

        self.dispatcher: AgentDispatcher | None = None

        self.discovery_event_subscriber: NCSubscriber[ClassDiscoveryRequestEvent] | None = None
        self.control_event_subscriber: JSSubscriber | None = None
        self.nc_publisher: NCPublisher[AgentClassDiscoveryResponseEvent] | None = None

        self.locale_handler = AgentLocaleHandler(locale_paths=locale_paths)

        self.health_port = health_port
        self._health_server: HTTPServer | None = None
        self._health_thread: threading.Thread | None = None

    def _create_health_handler(self) -> type[BaseHTTPRequestHandler]:
        """Creates a health check HTTP request handler with access to the runner instance."""
        runner = self

        class HealthHandler(BaseHTTPRequestHandler):
            def log_message(self, format: str, *args: object) -> None:
                # Suppress default logging to avoid cluttering logs
                pass

            def do_GET(self) -> None:
                if self.path == "/health":
                    self._handle_liveness()
                elif self.path == "/health/ready":
                    self._handle_readiness()
                else:
                    self.send_error(404, "Not Found")

            def _handle_liveness(self) -> None:
                """Simple liveness check - just confirms the process is running."""
                health_status = {
                    "status": "ok",
                    "agent_class": runner.agent_class,
                }
                response_body = json.dumps(health_status).encode("utf-8")

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(response_body)))
                self.end_headers()
                self.wfile.write(response_body)

            def _handle_readiness(self) -> None:
                """Readiness check - verifies all dependencies are available."""
                checks: dict[str, bool] = {}
                is_healthy = True

                # Check if runner is running
                checks["running"] = runner.running
                if not runner.running:
                    is_healthy = False

                # Check NATS connection
                nats_connected = runner.nc is not None and runner.nc.is_connected
                checks["nats"] = nats_connected
                if not nats_connected:
                    is_healthy = False

                # Check Redis connection by pinging
                redis_healthy = _check_redis(runner.redis)
                checks["redis"] = redis_healthy
                if not redis_healthy:
                    is_healthy = False

                health_status = {
                    "status": "ok" if is_healthy else "unhealthy",
                    "agent_class": runner.agent_class,
                    "checks": checks,
                }

                status_code = 200 if is_healthy else 503
                response_body = json.dumps(health_status).encode("utf-8")

                self.send_response(status_code)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(response_body)))
                self.end_headers()
                self.wfile.write(response_body)

        return HealthHandler

    def _is_port_available(self, port: int) -> bool:
        """Check if a port is available for binding."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("0.0.0.0", port))
                return True
            except OSError:
                return False

    def _find_free_port(self) -> int:
        """Find a random available port."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("0.0.0.0", 0))
            return s.getsockname()[1]

    def _start_health_server(self) -> None:
        """Starts the HTTP health check server in a background thread."""
        env_port = os.environ.get("AGENT_HEALTH_PORT")

        if env_port is not None:
            # User explicitly set port - use it or fail
            port = int(env_port)
            if not self._is_port_available(port):
                raise OSError(f"AGENT_HEALTH_PORT={port} is not available. Port is already in use.")
        elif self._is_port_available(self.health_port):
            # Default port is available
            port = self.health_port
        else:
            # Default port occupied, find a free one
            port = self._find_free_port()
            logger.warning(f"Default health port {self.health_port} is occupied, falling back to port {port}")

        handler_class = self._create_health_handler()
        self._health_server = HTTPServer(("0.0.0.0", port), handler_class)
        self._health_thread = threading.Thread(target=self._health_server.serve_forever, daemon=True)
        self._health_thread.start()
        logger.info(f"Health check server started on port {port}")

    def _stop_health_server(self) -> None:
        """Stops the HTTP health check server."""
        if self._health_server:
            self._health_server.shutdown()
            self._health_server = None
        if self._health_thread:
            self._health_thread.join(timeout=5)
            self._health_thread = None
        logger.debug("Health check server stopped")

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

        agent_config_specs = AgentConfigSpecs.from_agent_config_class(self.agent_config_type)

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

        # Start health check server
        self._start_health_server()

    async def stop(self):
        """
        Stops the agent by setting a stop event, unsubscribing, and closing the NATS connection.
        """
        if not self.running:
            logger.warning("AgentRunner is not running.")
            return

        logger.debug(f"Shutting down {self.agent_class}...")

        # Stop health check server first
        self._stop_health_server()
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
