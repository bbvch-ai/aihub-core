import asyncio
import copy
import logging

from aihub_lib.infrastructure.mongo.MongoSettings import MongoSettings
from aihub_lib.infrastructure.nats.NatsSettings import NatsSettings
from aihub_lib.infrastructure.redis.RedisSettings import RedisSettings
from aihub_lib.nats.events import ProcessStartEvent
from aihub_lib.nats.events.discovery.ClassDiscoveryRequestEvent import ClassDiscoveryRequestEvent
from aihub_lib.nats.events.discovery.EventSpecs import EventSpecs
from aihub_lib.nats.events.discovery.process.agent_in.AgentInSpecs import AgentInSpecs
from aihub_lib.nats.events.discovery.process.human_in.HumanInSpecs import HumanInSpecs
from aihub_lib.nats.events.discovery.process.ProcessClassDiscoveryResponseEvent import (
    ProcessClassDiscoveryResponseEvent,
)
from aihub_lib.nats.events.discovery.process.ProcessConfigSpecs import ProcessConfigSpecs
from aihub_lib.nats.events.discovery.process.program_in.ProgramInSpecs import ProgramInSpecs
from aihub_lib.nats.events.form.TemplateData import TemplateData
from aihub_lib.nats.publishers.NCPublisher import NCPublisher
from aihub_lib.nats.subscribers.JSSubscriber import JSSubscriber
from aihub_lib.nats.subscribers.NCSubscriber import NCSubscriber
from aihub_lib.nats.subscribers.process.ProcessJSSubscriber import ProcessJSSubscriber
from aihub_lib.nats.subscribers.process.ProcessNCSubscriber import ProcessNCSubscriber
from aihub_lib.nats.topic_managers.process.ProcessClassTopicManager import ProcessClassTopicManager
from aihub_lib.nats.topic_managers.process.ProcessTopicManager import ProcessTopicManager
from aihub_lib.nats.topics.discovery.process.ProcessClassDiscoveryTopic import ProcessClassDiscoveryTopic
from aihub_lib.processes.ProcessConfig import ProcessConfig
from aihub_lib.routes.health.dto.HealthResponse import ProcessHealthChecks
from aihub_lib.routes.health.health_checks import check_nats_sync, check_redis_sync
from aihub_lib.routes.health.HealthServer import HealthCheckProvider, HealthServer
from mongoengine import connect
from mongoengine.connection import get_connection
from nats.aio.client import Client as NATS
from nats.js import JetStreamContext
from redis.asyncio import Redis

from aihub_process.agentic_processes.AgenticProcess import AgenticProcess
from aihub_process.delegators.agent.AgentDelegator import AgentDelegator
from aihub_process.delegators.process.ProcessDelegator import ProcessDelegator
from aihub_process.dispatchers.ProcessDispatcher import ProcessDispatcher
from aihub_process.i18n.ProcessLocaleHandler import ProcessLocaleHandler

logger = logging.getLogger(__name__)


class ProcessRunner(HealthCheckProvider):
    """
    The process runner is responsible for connecting with external services like NATs, JetStream, and Redis, as well
    as running the process through a process dispatcher.
    The runner is also responsible for making the process discoverable by responding to discovery requests.

    The process_config parameter should be a form-mode ProcessConfig instance (created via as_form()).
    It contains:
    - Configurable fields: FormKit elements that define the form for UI configuration
    - Non-configurable fields: Actual values that are deployment-specific and not user-editable

    The form is automatically extracted from process_config.to_formkit_form().
    Non-configurable values are merged with incoming config by the dispatcher.

    Class-level metadata (name, description, icon) is extracted from the process_type class variables.
    """

    def __init__(
        self,
        process_type: type[AgenticProcess],
        process_config: ProcessConfig,
        templates: list[ProcessConfig] | None = None,
        locale_paths: list[str] | None = None,
        health_port: int = 8090,
    ):
        if not isinstance(process_type, type):
            raise ValueError("process_type must be a class, not an instance or module.")
        if not issubclass(process_type, AgenticProcess):
            raise ValueError("process_type must be a subclass of AgenticProcess.")

        self.process_type = process_type
        self.process_config = process_config
        self.templates = templates or []
        self.process_config_type = process_config.__class__

        self.name = process_type.name
        self.description = process_type.description
        self.icon = process_type.icon

        self.form = process_config.to_formkit_form()

        self.running = False
        self._stop_signal = asyncio.Event()
        self._loop_task: asyncio.Task | None = None

        self.process_class = self.process_type.__name__
        self.topic_manager = ProcessClassTopicManager(process_class=self.process_class)

        self.nc: NATS | None = None
        self.js: JetStreamContext | None = None
        self.redis: Redis | None = None

        self.dispatcher: ProcessDispatcher | None = None

        self.agent_delegator: AgentDelegator | None = None
        self.process_delegator: ProcessDelegator | None = None

        self.discovery_event_subscriber: NCSubscriber[ClassDiscoveryRequestEvent] | None = None
        self.work_event_subscriber: JSSubscriber | None = None
        self.nc_publisher: NCPublisher[ProcessClassDiscoveryResponseEvent] | None = None

        self.locale_handler = ProcessLocaleHandler(locale_paths=locale_paths)

        self._loop: asyncio.AbstractEventLoop | None = None
        self._health_server = HealthServer(
            provider=self,
            default_port=health_port,
            port_env_var="PROCESS_HEALTH_PORT",
        )

    @property
    def entity_name(self) -> str:
        return self.process_class

    @property
    def entity_type(self) -> str:
        return "process"

    def get_readiness_checks(self) -> ProcessHealthChecks:
        return ProcessHealthChecks(
            running=self.running,
            nats=check_nats_sync(self.nc, self._loop) if self._loop else False,
            redis=check_redis_sync(self.redis, self._loop) if self._loop else False,
        )

    async def discovery_handler(self, event: ClassDiscoveryRequestEvent, topic: ProcessClassDiscoveryTopic):
        """
        Responds to discovery requests by publishing a ProcessDiscoveryResponseEvent that includes the basic
        process configuration.
        """
        if topic.process_class not in [self.process_class, "*"]:
            logger.debug(f"Discovery request for {topic.process_class} does not match this process.")
            return

        logger.debug(f"Received discovery request for {topic.process_class}.")
        subject = self.topic_manager.get_process_class_discovery_subject_response(topic.call_id)

        human_inputs: list[HumanInSpecs] = [
            HumanInSpecs(
                name=human_work_event.display_name_from_class(),
                description=human_work_event.display_description_from_class(),
                route=human_in.route,
                method=human_in.method,
                is_process_start=issubclass(human_work_event, ProcessStartEvent),
                event_specs=EventSpecs(
                    event_name=human_work_event.event_name_from_class(),
                    event_schema=copy.deepcopy(human_work_event.to_form_submission_model().model_json_schema()),
                    event_parents=human_work_event.parent_event_names_from_class(),
                ),
                form=([] if not human_in.start_form else human_in.start_form.to_formkit_form()),
            )
            for human_work_event, human_in in self.process_type.get_events_with_human_in()
        ]

        program_inputs: list[ProgramInSpecs] = [
            ProgramInSpecs(
                route=process_in.route,
                method=process_in.method,
                is_process_start=issubclass(process_work_event, ProcessStartEvent),
                event_specs=EventSpecs.from_event_class(process_work_event),
            )
            for process_work_event, process_in in self.process_type.get_events_with_process_in()
        ]

        agent_inputs: list[AgentInSpecs] = [
            AgentInSpecs(
                agent_class=agent_in.agent_class,
                agent_id=agent_in.agent_id,
                is_process_start=issubclass(agent_work_event, ProcessStartEvent),
                event_specs=EventSpecs.from_event_class(agent_work_event),
            )
            for agent_work_event, agent_in in self.process_type.get_events_with_agent_in()
        ]

        process_config_specs = ProcessConfigSpecs.from_process_config(self.process_config, self.process_class)

        templates_data: list[TemplateData] = [t.to_template_data(self.process_config) for t in self.templates]

        process_discovery_response_event = ProcessClassDiscoveryResponseEvent(
            process_class=self.process_class,
            name=self.name,
            description=self.description,
            icon=self.icon,
            form=self.form,
            process_config_specs=process_config_specs,
            human_inputs=human_inputs,
            program_inputs=program_inputs,
            agent_inputs=agent_inputs,
            templates=templates_data,
        )
        await self.nc_publisher.publish_event(process_discovery_response_event, subject)

    async def start(self):
        """
        Connects to all external services and starts the process dispatcher with connecting it to a JetStream stream.
        To connect the process to all process entities, we must also start the individual delegators.
        """
        if self.running:
            logger.warning("ProcessRunner is already running.")
            return

        self.running = True
        self._stop_signal.clear()
        self._loop = asyncio.get_running_loop()

        # Connect to MongoDB (skip if already connected)
        try:
            get_connection()
        except Exception:
            connect(
                host=MongoSettings().CONNECTION_STRING.get_secret_value(),
                uuidRepresentation="standard",
            )

        self.nc = await NatsSettings.create_client()
        self.js = self.nc.jetstream(timeout=60, publish_async_max_pending=10_000)
        self.redis = RedisSettings.create_client()

        self.dispatcher = ProcessDispatcher(
            self.process_type,
            self.process_config,
            self.nc,
            self.js,
            self.redis,
            self.topic_manager,
            self.locale_handler,
        )
        await self.dispatcher.start()

        self.agent_delegator = AgentDelegator(
            process_type=self.process_type,
            nc=self.nc,
            js=self.js,
            topic_manager=self.topic_manager,
            queue_group=f"agent_delegator_{self.process_class}",
        )
        await self.agent_delegator.start()

        self.process_delegator = ProcessDelegator(
            self.process_type,
            self.nc,
            self.js,
            self.topic_manager,
            queue_group=f"process_delegator_{self.process_class}",
        )
        await self.process_delegator.start()

        self.nc_publisher = NCPublisher(f"{self.process_class}RunnerDiscoveryResponse", self.nc)
        self.discovery_event_subscriber = ProcessNCSubscriber.for_process_class_discovery_request_events(
            self.nc,
            ProcessTopicManager(),
            self.discovery_handler,
            subscriber_name=f"{self.process_class}RunnerDiscoveryRequest",
        )
        await self.discovery_event_subscriber.start()

        self.work_event_subscriber = ProcessJSSubscriber.for_process_class_work_events(
            self.nc,
            self.topic_manager,
            handler=self.dispatcher.handle_event,
            js=self.js,
            queue_group=f"process_runner_{self.process_class}",
            subscriber_name=f"{self.process_class}RunnerWorkEvents",
        )
        await self.work_event_subscriber.start()

        logger.debug(f"{self.process_class} is now running and subscribed to incoming messages.")
        self._loop_task = asyncio.create_task(self._run_loop())

        # Start health check server
        self._health_server.start()

    async def stop(self):
        """
        Stops the process by setting a stop event, unsubscribing, and closing the NATS connection.
        Also stops all delegators.
        """
        if not self.running:
            logger.warning("ProcessRunner is not running.")
            return

        logger.debug(f"Shutting down {self.process_class}...")

        # Stop health check server first
        self._health_server.stop()
        self._stop_signal.set()

        if self._loop_task is not None:
            try:
                await self._loop_task
            except asyncio.CancelledError:
                pass
        else:
            logger.exception(f"Loop task was not running for {self.process_class}.")

        self.running = False

        await self.work_event_subscriber.stop()
        await self.dispatcher.stop()

        await self.agent_delegator.stop()
        await self.process_delegator.stop()

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
        logger.debug(f"Starting {self.process_class}")
        await self.start()
        try:
            await self._stop_signal.wait()
        except KeyboardInterrupt:
            await self.stop()
