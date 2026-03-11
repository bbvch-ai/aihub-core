import logging
from typing import Self

from nats.aio.client import Client as NATS
from nats.js import JetStreamContext
from swiss_ai_hub.core.events import BaseEvent, ClassDiscoveryRequestEvent, EventSpecs
from swiss_ai_hub.core.events.process import (
    AgentInSpecs,
    HumanInSpecs,
    HumanWorkEvent,
    ProcessClassDiscoveryResponseEvent,
    ProcessConfigSpecs,
    ProcessEvent,
    ProcessStartEvent,
    ProgramInSpecs,
    ProgramWorkEvent,
    WorkEvent,
    WorkRequestEvent,
)
from swiss_ai_hub.core.form import InputText
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.infrastructure import NatsSettings
from swiss_ai_hub.core.processes import ProcessConfig
from swiss_ai_hub.core.publishers import JSPublisher, NCPublisher
from swiss_ai_hub.core.subscribers import JSSubscriber, NCSubscriber, ProcessJSSubscriber, ProcessNCSubscriber
from swiss_ai_hub.core.topic_managers import (
    ProcessInstanceTopicManager,
    ProcessTopicManager,
    ProcessWalkthroughTopicManager,
)
from swiss_ai_hub.core.topics.discovery.process import ProcessClassDiscoveryTopic
from swiss_ai_hub.core.topics.process import ProcessInstanceTopic

from swiss_ai_hub.api.i18n.api_locale_handler import ApiLocaleHandler
from swiss_ai_hub.api.routes.process.dto.process_class_dto import ProcessClassDTO
from swiss_ai_hub.api.runners.api_test_runner import ApiTestRunner
from swiss_ai_hub.api.runners.simulation.process.events.custom_process_stop_event import CustomProcessStopEvent
from swiss_ai_hub.api.runners.simulation.process.events.human_b_work import HumanBWork
from swiss_ai_hub.api.runners.simulation.process.events.human_b_work_reqeust import HumanBWorkRequest
from swiss_ai_hub.api.runners.simulation.process.events.human_start_work import HumanStartEvent
from swiss_ai_hub.api.services.process_endpoints_discovery_service import ProcessEndpointsDiscoveryService

logger = logging.getLogger(__name__)


class SimulatedProcessApiTestRunner(ApiTestRunner):
    """
    A specialized test runner simulating an process's behavior within the AI Hub environment.

    ### Why This Class?
    When developing or testing workflows that interact with processes, you may need a controlled,
    simulated environment. `SimulatedProcessApiTestRunner`:
    - Connects to NATS and JetStream.
    - Subscribes to work events for a given process instance.
    - Publishes simulated events (human work, agent work, program work) as if
      an process were responding to a work request.

    This allows you to test end-to-end workflows (from discovery to event consumption) without needing
    a real process implementation.

    ### Features
    - **Process Identification:** Uses `process_class` and `process_id` to scope
      events to a particular process instance.
    - **Simulated Events:** You can provide a list of events that will be published
      after a WorkReqeustEvent arrives.
    - **Discovery Handling:** Responds to discovery requests with a mock `ProcessClassDiscoveryResponseEvent`,
      ensuring clients can "find" this simulated process class.

    ### Lifecycle
    - On `run()`:
      1. Connect to NATS and JetStream.
      2. Subscribe to discovery requests and process control events.
      3. When a StartEvent is received, publish the simulated events followed by a StopEvent.
      4. Then start the server via the parent `ApiTestRunner`.

    ### Example
    ```python
    runner = SimulatedProcessApiTestRunner(process_class="my_process_class", process_id="my_process_id")
    await runner.run()  # Launches the simulation and HTTP server
    ```
    """

    def __init__(
        self,
        process_class: str,
        process_id: str,
        simulated_events: list[tuple[type[ProcessEvent], ProcessEvent]] | None = None,
    ):
        super().__init__()
        self.process_class = process_class
        self.process_id = process_id
        self.topic_manager = ProcessInstanceTopicManager(process_class=process_class, process_id=process_id)

        self.nc: NATS | None = None
        self.js: JetStreamContext | None = None

        self.process_work_event_subscriber: JSSubscriber[WorkRequestEvent] | None = None
        self.js_publisher: JSPublisher | None = None

        self.nc_publisher: NCPublisher[ProcessClassDiscoveryResponseEvent] | None = None
        self.discovery_subscriber: NCSubscriber[ClassDiscoveryRequestEvent] | None = None

        self.simulated_events: list[tuple[type[ProcessEvent], ProcessEvent]] = simulated_events or []

        self.human_inputs: list[HumanInSpecs] = []
        self.program_inputs: list[ProgramInSpecs] = []
        self.agent_inputs: list[AgentInSpecs] = []

    async def simulate_process(self, event: WorkEvent, topic: ProcessInstanceTopic):
        """
        Handler for work events targeting this process instance. If a WorkEvent arrives,
        publish the simulated events in sequence.

        This simulates an process run, where after receiving a start signal, the process responds
        with chunks, cost events, etc., and finally a stop signal.
        """
        for in_event_type, out_event in self.simulated_events:
            if event.event_name == in_event_type.event_name_from_class():
                await self.publish_event(out_event, topic)

    async def discovery_handler(self, event: ClassDiscoveryRequestEvent, topic: ProcessClassDiscoveryTopic):
        """
        Responds to a discovery request by publishing a `ProcessClassDiscoveryResponseEvent`.
        This simulates the process class being discoverable by clients, providing metadata and start events.
        """
        logger.debug(f"Received discovery request for {self.process_class}")
        subject = self.topic_manager.get_process_class_discovery_subject_response(topic.call_id)
        process_discovery_response_event = ProcessClassDiscoveryResponseEvent(
            process_class=self.process_class,
            name=LocaleString(en=self.process_class),
            description=LocaleString(en=""),
            icon="mage:broadcast",
            form=[],
            human_inputs=self.human_inputs,
            program_inputs=self.program_inputs,
            agent_inputs=self.agent_inputs,
            process_config_specs=ProcessConfigSpecs.from_process_config_class(ProcessConfig),
        )
        await self.nc_publisher.publish_event(process_discovery_response_event, subject)

    async def publish_event(self, event: BaseEvent, topic: ProcessInstanceTopic):
        """
        Publish a given event (ControlEvent or DisplayEvent) to the appropriate subject based
        on the process walkthrough ID specified in the `topic`.
        """
        thread_topic_manager = ProcessWalkthroughTopicManager.from_process_instance_topic_manager(
            self.topic_manager,
            process_walkthrough_id=topic.process_walkthrough_id,
        )
        if event.is_work_event:
            subject = thread_topic_manager.get_subject_for_work_event_in_walkthrough(event.event_name, event.event_id)
            logger.debug(f"Publishing work event {event.event_name} to {subject}")
            await self.js_publisher.publish_event(event, subject)

        if event.is_work_request_event:
            subject = thread_topic_manager.get_subject_for_work_request_event_in_walkthrough(
                event.event_name, event.event_id
            )
            logger.debug(f"Publishing work request event {event.event_name} to {subject}")
            event.process_id = self.process_id
            await self.js_publisher.publish_event(event, subject)

    async def start_simulation(self):
        """
        Orchestrates the simulation:
        1. Connect to NATS.
        2. Set up publishers and subscribers (discovery requests, process work request events).
        3. Start the parent ApiTestRunner's run method to launch the server.

        Requires that at least one simulated event is provided; otherwise, it's a no-op.
        """
        assert len(self.simulated_events) > 0, "No simulated events provided"

        self.nc = await NatsSettings.create_client()

        self.human_inputs = [
            HumanInSpecs(
                name=LocaleString(en=HumanStartEvent.event_name_from_class()),
                description=LocaleString(en=f"{HumanStartEvent.event_name_from_class()} description"),
                route="/human_input_0",
                method="POST",
                is_process_start=True,
                event_specs=EventSpecs.from_event_class(HumanStartEvent),
                form=HumanStartEvent(
                    payload=InputText(
                        label=LocaleString(en=f"This is some label for {HumanStartEvent.event_name_from_class()}")
                    )
                ).to_formkit_form(),
            )
        ]

        human_endpoints = 1
        program_endpoints = 0
        for in_event_type, out_event in self.simulated_events:
            if issubclass(in_event_type, HumanWorkEvent) and not issubclass(in_event_type, ProcessStartEvent):
                self.human_inputs.append(
                    HumanInSpecs(
                        name=LocaleString(en=in_event_type.event_name_from_class()),
                        description=LocaleString(en=f"{in_event_type.event_name_from_class()} description"),
                        route=f"/human_input_{human_endpoints}",
                        method="POST",
                        is_process_start=False,
                        event_specs=EventSpecs.from_event_class(in_event_type),
                    )
                )
                human_endpoints += 1
            if issubclass(in_event_type, ProgramWorkEvent) and not issubclass(in_event_type, ProcessStartEvent):
                self.program_inputs.append(
                    ProgramInSpecs(
                        route=f"/program_input_{program_endpoints}",
                        method="POST",
                        is_process_start=False,
                        event_specs=EventSpecs.from_event_class(in_event_type),
                    )
                )
                program_endpoints += 1

        self.nc_publisher = NCPublisher(f"Simulated{self.process_class}ApiTestRunnerDiscoveryResponse", self.nc)
        self.discovery_subscriber = ProcessNCSubscriber.for_process_class_discovery_request_events(
            self.nc,
            ProcessTopicManager(),
            self.discovery_handler,
            subscriber_name=f"Simulated{self.process_class}ApiTestRunnerDiscoveryRequest",
        )
        await self.discovery_subscriber.start()

        self.js = self.nc.jetstream()
        self.process_work_event_subscriber = ProcessJSSubscriber.for_process_instance_work_events(
            self.nc,
            self.topic_manager,
            js=self.js,
            handler=self.simulate_process,
            queue_group="simulated-process-runner-queue-group",
            subscriber_name=f"Simulated{self.process_class}ApiTestRunnerWorkEvents",
        )
        await self.process_work_event_subscriber.start()

        self.js_publisher = JSPublisher(f"Simulated{self.process_class}ApiTestRunner", self.js)

        if hasattr(self._api_app.state, "process_controller"):
            discovery_service = ProcessEndpointsDiscoveryService(
                nc=self.nc,
                api_app=self._api_app,
                controller=self._api_app.state.process_controller,
                locale_handler=ApiLocaleHandler(),
                discovery_interval=60,
            )
            process_class_dto = ProcessClassDTO(
                process_class=self.process_class,
                name=LocaleString(en=self.process_class),
                description=LocaleString(en=""),
                icon="mage:broadcast",
                form=[],
                process_config_specs=ProcessConfigSpecs.from_process_config_class(ProcessConfig),
                human_inputs=self.human_inputs,
                program_inputs=self.program_inputs,
                agent_inputs=self.agent_inputs,
                is_online=True,
            )
            discovery_service._register_class_endpoints(process_class_dto)

    async def run(self):
        await self.start_simulation()
        await super().run()

    def with_simple_human_only_process_events(self) -> Self:
        """
        A convenience method to populate a standard sequence of process events with just two humans involved.
        """
        self.simulated_events = [
            (
                HumanStartEvent,
                HumanBWorkRequest(
                    forms=[HumanBWork(payload=InputText(label=LocaleString(en="This is some label for HumanBWork")))]
                ),
            ),
            (HumanBWork, CustomProcessStopEvent(payload="Done")),
        ]
        return self
