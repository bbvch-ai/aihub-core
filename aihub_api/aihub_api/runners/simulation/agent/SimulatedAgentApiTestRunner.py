import logging

from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.agents.visualizers.types.WorkflowGraph import WorkflowGraph
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.infrastructure.nats.NatsSettings import NatsSettings
from aihub_lib.nats.events import (
    BaseEvent,
    ChunkEvent,
    ControlEvent,
    LLMStopEvent,
    StartEvent,
    StopEvent,
    UserMessageEvent,
)
from aihub_lib.nats.events.cost.LLMCostEvent import LLMCostEvent
from aihub_lib.nats.events.discovery.agent.AgentClassDiscoveryResponseEvent import (
    AgentClassDiscoveryResponseEvent,
    AgentConfigSpecs,
    EventSpecs,
)
from aihub_lib.nats.events.discovery.agent.AgentInstanceDiscoveryResponseEvent import (
    AgentInstanceDiscoveryResponseEvent,
)
from aihub_lib.nats.events.discovery.ClassDiscoveryRequestEvent import ClassDiscoveryRequestEvent
from aihub_lib.nats.events.discovery.InstanceDiscoveryRequestEvent import InstanceDiscoveryRequestEvent
from aihub_lib.nats.events.semantic import Message
from aihub_lib.nats.publishers.JSPublisher import JSPublisher
from aihub_lib.nats.publishers.NCPublisher import NCPublisher
from aihub_lib.nats.subscribers.agent.AgentJSSubscriber import AgentJSSubscriber
from aihub_lib.nats.subscribers.agent.AgentNCSubscriber import AgentNCSubscriber
from aihub_lib.nats.subscribers.JSSubscriber import JSSubscriber
from aihub_lib.nats.subscribers.NCSubscriber import NCSubscriber
from aihub_lib.nats.topic_managers.agents.AgentInstanceTopicManager import AgentInstanceTopicManager
from aihub_lib.nats.topic_managers.agents.AgentThreadTopicManager import AgentThreadTopicManager
from aihub_lib.nats.topic_managers.agents.AgentTopicManager import AgentTopicManager
from aihub_lib.nats.topics.agents.AgentInstanceTopic import AgentInstanceTopic
from aihub_lib.nats.topics.discovery.agent.AgentClassDiscoveryTopic import AgentClassDiscoveryTopic
from nats.aio.client import Client as NATS
from nats.js import JetStreamContext

from aihub_api.i18n.ApiLocaleHandler import ApiLocaleHandler
from aihub_api.runners.ApiTestRunner import ApiTestRunner
from aihub_api.services.AgentEndpointsDiscoveryService import AgentEndpointsDiscoveryService

logger = logging.getLogger(__name__)


class SimulatedAgentApiTestRunner(ApiTestRunner):
    """
    A specialized test runner simulating an agent’s behavior within the AI Hub environment.

    ### Why This Class?
    When developing or testing workflows that interact with agents, you may need a controlled,
    simulated environment. `SimulatedAgentApiTestRunner`:
    - Connects to NATS and JetStream.
    - Subscribes to control events for a given agent instance.
    - Publishes simulated events (chunks, costs, etc.) as if an agent were responding to a start event.

    This allows you to test end-to-end workflows (from discovery to event consumption) without needing
    a real agent implementation.

    ### Features
    - **Agent Identification:** Uses `agent_class` and `agent_id` to scope events to a particular agent instance.
    - **Simulated Events:** You can provide a list of events that will be published after a StartEvent arrives.
      By default, no events are provided, but `with_simple_chunk_events()` can populate a standard example.
    - **Discovery Handling:** Responds to discovery requests with a mock `AgentDiscoveryResponseEvent`,
      ensuring clients can "find" this simulated agent.

    ### Lifecycle
    - On `run()`:
      1. Connect to NATS and JetStream.
      2. Subscribe to discovery requests and agent control events.
      3. When a StartEvent is received, publish the simulated events followed by a StopEvent.
      4. Then start the server via the parent `ApiTestRunner`.

    ### Example
    ```python
    runner = SimulatedAgentApiTestRunner(agent_class="my_agent_class", agent_id="my_agent_id")
    runner.with_simple_chunk_events()
    await runner.run()  # Launches the simulation and HTTP server
    ```
    """

    def __init__(
        self,
        agent_class: str,
        agent_id: str,
        simulated_events: list[BaseEvent] | None = None,
        start_events: list[EventSpecs] | None = None,
        stop_events: list[EventSpecs] | None = None,
        hitl_request_events: list[EventSpecs] | None = None,
        hitl_response_events: list[EventSpecs] | None = None,
    ):
        super().__init__()
        self.agent_class = agent_class
        self.agent_id = agent_id
        self.topic_manager = AgentInstanceTopicManager(agent_class=agent_class, agent_id=agent_id)

        self.nc: NATS | None = None
        self.js: JetStreamContext | None = None

        self.agent_control_event_subscriber: JSSubscriber[ControlEvent] | None = None
        self.js_publisher: JSPublisher | None = None

        self.nc_publisher: NCPublisher[AgentInstanceDiscoveryResponseEvent] | None = None
        self.discovery_subscriber: NCSubscriber[InstanceDiscoveryRequestEvent] | None = None

        self.simulated_events: list[BaseEvent] = simulated_events or []

        self.start_events: list[EventSpecs] | None = start_events
        self.stop_events: list[EventSpecs] | None = stop_events
        self.hitl_request_events: list[EventSpecs] | None = hitl_request_events
        self.hitl_response_events: list[EventSpecs] | None = hitl_response_events

        self.default_agent_config: AgentConfig = AgentConfig(
            agent_class=self.agent_class,
            agent_id=self.agent_id,
            name=LocaleString(de="Test Agent"),
            description=LocaleString(de="Test Agent Description"),
        )

    async def simulate_agent(self, event: ControlEvent, topic: AgentInstanceTopic):
        """
        Handler for control events targeting this agent instance. If a StartEvent arrives,
        publish the simulated events in sequence, followed by a StopEvent to conclude the run.

        This simulates an agent run, where after receiving a start signal, the agent responds
        with chunks, cost events, etc., and finally a stop signal.
        """
        if event.is_start_event:
            for sim_event in self.simulated_events:
                await self.publish_event(sim_event, topic)
            if not any(e.is_stop_event for e in self.simulated_events):
                await self.publish_event(StopEvent(), topic)

    async def discovery_handler(self, event: ClassDiscoveryRequestEvent, topic: AgentClassDiscoveryTopic):
        """
        Responds to a discovery request by publishing an `AgentDiscoveryResponseEvent`.
        This simulates the agent being discoverable by clients, providing metadata and start events.
        """
        logger.debug(f"Received discovery request for {self.agent_class} ({self.agent_id})")
        subject = self.topic_manager.get_agent_class_discovery_subject_response(topic.call_id)
        agent_discovery_response_event = AgentClassDiscoveryResponseEvent(
            agent_class=self.agent_class,
            is_conversational=True,
            start_events=self.start_events,
            stop_events=self.stop_events,
            hitl_request_events=self.hitl_request_events or [],
            hitl_response_events=self.hitl_response_events or [],
            network_graph=WorkflowGraph(directed=True, multigraph=False, graph={}, nodes=[], links=[]),
            agent_config_specs=AgentConfigSpecs.from_agent_config(self.default_agent_config, form=[]),
            default_agent_config=self.default_agent_config,
        )
        await self.nc_publisher.publish_event(agent_discovery_response_event, subject)

    async def publish_event(self, event: BaseEvent, topic: AgentInstanceTopic):
        """
        Publish a given event (ControlEvent or DisplayEvent) to the appropriate subject based
        on the thread and run specified in the `topic`. Uses `AgentThreadTopicManager` to
        derive the correct subject.

        Control events are published to control_event subjects,
        and display events to display_event subjects.
        """
        thread_topic_manager = AgentThreadTopicManager.from_agent_instance_topic_manager(
            self.topic_manager,
            thread_id=topic.thread_id,
            display_id=topic.display_id,
            run_id=topic.run_id,
        )
        if event.is_control_event:
            subject = thread_topic_manager.get_subject_for_control_event_in_thread(event.event_name, event.event_id)
            logger.debug(f"Publishing control event {event.event_name} to {subject}")
            await self.js_publisher.publish_event(event, subject)

        if event.is_display_event:
            subject = thread_topic_manager.get_subject_for_display_event_in_thread(event.event_name, event.event_id)
            logger.debug(f"Publishing display event {event.event_name} to {subject}")
            await self.js_publisher.publish_event(event, subject)

    async def start_simulation(self):
        """
        Orchestrates the simulation:
        1. Connect to NATS.
        2. Set up publishers and subscribers (discovery requests, agent control events).
        3. Start the parent ApiTestRunner's run method to launch the server.

        Requires that at least one simulated event is provided; otherwise, it's a no-op.
        """
        assert len(self.simulated_events) > 0, "No simulated events provided"

        self.nc = NATS()
        await self.nc.connect(servers=[NatsSettings().ENDPOINT])

        if self.start_events is None:
            self.start_events = [
                EventSpecs.from_event_class(StartEvent),
                EventSpecs.from_event_class(UserMessageEvent),
            ]
        if self.stop_events is None:
            self.stop_events = [
                EventSpecs.from_event_class(StopEvent),
                EventSpecs.from_event_class(LLMStopEvent),
            ]
        if self.hitl_request_events is None:
            self.hitl_request_events = []
        if self.hitl_response_events is None:
            self.hitl_response_events = []

        self.nc_publisher = NCPublisher(f"Simulated{self.agent_class}ApiTestRunnerDiscoveryResponse", self.nc)
        self.discovery_subscriber = AgentNCSubscriber.for_agent_class_discovery_request_events(
            self.nc,
            AgentTopicManager(),
            self.discovery_handler,
            subscriber_name=f"Simulated{self.agent_class}ApiTestRunnerDiscoveryRequest",
        )
        await self.discovery_subscriber.start()

        self.js = self.nc.jetstream()
        self.agent_control_event_subscriber = AgentJSSubscriber.for_agent_instance_control_events(
            self.nc,
            self.topic_manager,
            js=self.js,
            handler=self.simulate_agent,
            queue_group="simulated-agent-runner-queue-group",
            subscriber_name=f"Simulated{self.agent_class}ApiTestRunnerControlEvents",
        )
        await self.agent_control_event_subscriber.start()

        self.js_publisher = JSPublisher(f"Simulated{self.agent_class}ApiTestRunner", self.js)

        if hasattr(self._api_app.state, "agent_controller"):
            AgentEndpointsDiscoveryService(
                nc=self.nc,
                api_app=self._api_app,
                controller=self._api_app.state.agent_controller,
                locale_handler=ApiLocaleHandler(),
                discovery_interval=60,
            )._register_agent_endpoints(
                agent_class=self.agent_class,
                agent_id=self.agent_id,
                start_events=self.start_events,
                stop_events=self.stop_events,
                hitl_request_events=self.hitl_request_events,
                hitl_response_events=self.hitl_response_events,
                config=self.default_agent_config,
            )
        else:
            logger.warning("Unable to start AgentEndpointsDiscoveryService due to missing state.agent_controller")

    async def run(self):
        await self.start_simulation()
        await super().run()

    def with_simple_chunk_events(self) -> "SimulatedAgentApiTestRunner":
        """
        A convenience method to populate a standard sequence of chunk and cost events, simulating
        a typical LLM-based agent responding with textual chunks and cost metrics.

        This returns `self` so it can be chained:
        ```python
        runner = SimulatedAgentApiTestRunner("my_class", "my_id").with_simple_chunk_events()
        ```

        The simulated_events array will contain two ChunkEvents and two LLMCostEvents.
        """
        model_name = "gpt-4"
        self.simulated_events = [
            ChunkEvent(content="First chunk.\n", model_name=model_name),
            LLMCostEvent(
                llm_name=model_name,
                prompt_token_count=9,
                completion_token_count=15,
                embedding_token_count=0,
                prompt_tokens_costs=0.1,
                completion_tokens_costs=0.3,
                embedding_tokens_costs=0.05,
            ),
            ChunkEvent(content="Second chunk", model_name=model_name),
            LLMCostEvent(
                llm_name=model_name,
                prompt_token_count=7,
                completion_token_count=16,
                embedding_token_count=0,
                prompt_tokens_costs=0.1,
                completion_tokens_costs=0.3,
                embedding_tokens_costs=0.05,
            ),
            LLMStopEvent(
                output_messages=[
                    Message.from_string(role="assistant", content="First chunk.\nSecond chunk"),
                ]
            ),
        ]
        return self
