import logging
from typing import Self

from nats.aio.client import Client as NATS
from nats.js import JetStreamContext
from swiss_ai_hub.core.agents import AgentConfig
from swiss_ai_hub.core.agents import WorkflowGraph
from swiss_ai_hub.core.events.agent import ControlEvent
from swiss_ai_hub.core.events.agent import StartEvent
from swiss_ai_hub.core.events.agent import StopEvent
from swiss_ai_hub.core.events.agent import LLMCostEvent
from swiss_ai_hub.core.events.agent import AgentClassDiscoveryResponseEvent
from swiss_ai_hub.core.events.agent import AgentConfigSpecs
from swiss_ai_hub.core.events.agent import ChunkEvent
from swiss_ai_hub.core.events import BaseEvent
from swiss_ai_hub.core.events import ClassDiscoveryRequestEvent
from swiss_ai_hub.core.events import EventSpecs
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.infrastructure import NatsSettings
from swiss_ai_hub.core.publishers import JSPublisher
from swiss_ai_hub.core.publishers import NCPublisher
from swiss_ai_hub.core.subscribers import AgentJSSubscriber
from swiss_ai_hub.core.subscribers import AgentNCSubscriber
from swiss_ai_hub.core.subscribers import JSSubscriber
from swiss_ai_hub.core.subscribers import NCSubscriber
from swiss_ai_hub.core.topic_managers import AgentInstanceTopicManager
from swiss_ai_hub.core.topic_managers import AgentThreadTopicManager
from swiss_ai_hub.core.topic_managers import AgentTopicManager
from swiss_ai_hub.core.topics.agents import AgentInstanceTopic
from swiss_ai_hub.core.topics import AgentClassDiscoveryTopic

from swiss_ai_hub.bot.runners.bot_test_runner import BotTestRunner

logger = logging.getLogger(__name__)


class SimulatedAgentBotTestRunner(BotTestRunner):
    """
    A specialized test runner simulating an agent’s behavior within the AI Hub environment.

    ### Why This Class?
    When developing or testing workflows that interact with agents, you may need a controlled,
    simulated environment. `SimulatedAgentBotsTestRunner`:
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
      4. Then start the server via the parent `BotsTestRunner`.

    ### Example
    ```python
    runner = SimulatedAgentBotsTestRunner(agent_class="my_agent_class", agent_id="my_agent_id")
    runner.with_simple_chunk_events()
    await runner.run()  # Launches the simulation and HTTP server
    ```
    """

    def __init__(
        self,
        agent_class: str,
        agent_id: str,
        simulated_events: list[BaseEvent] | None = None,
        conversation_ttl_days: float = 30,
    ):
        super().__init__(conversation_ttl_days=conversation_ttl_days)
        self.agent_class = agent_class
        self.agent_id = agent_id
        self.topic_manager = AgentInstanceTopicManager(agent_class=agent_class, agent_id=agent_id)

        self.nc: NATS | None = None
        self.js: JetStreamContext | None = None

        self.agent_control_event_subscriber: JSSubscriber[ControlEvent] | None = None
        self.js_publisher: JSPublisher | None = None

        self.nc_publisher: NCPublisher[AgentClassDiscoveryResponseEvent] | None = None
        self.discovery_subscriber: NCSubscriber[ClassDiscoveryRequestEvent] | None = None

        self.simulated_events: list[BaseEvent] = simulated_events or []

        self.agent_config: AgentConfig = AgentConfig(
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
            await self.publish_event(StopEvent(), topic)

    async def discovery_handler(self, event: ClassDiscoveryRequestEvent, topic: AgentClassDiscoveryTopic):
        """
        Responds to a class discovery request by publishing an `AgentClassDiscoveryResponseEvent`.
        This simulates the agent being discoverable by clients, providing metadata and start events.
        """
        subject = self.topic_manager.get_agent_class_discovery_subject_response(topic.call_id)
        start_events = [EventSpecs.from_event_class(StartEvent)]
        stop_events = [EventSpecs.from_event_class(StopEvent)]
        hitl_request_events = []
        hitl_response_events = []
        agent_discovery_response_event = AgentClassDiscoveryResponseEvent(
            agent_class=self.agent_class,
            name=self.agent_config.name,
            description=self.agent_config.description,
            icon=self.agent_config.icon,
            is_conversational=True,
            start_events=start_events,
            stop_events=stop_events,
            hitl_request_events=hitl_request_events,
            hitl_response_events=hitl_response_events,
            network_graph=WorkflowGraph(directed=True, multigraph=False, graph={}, nodes=[], links=[]),
            form=self.agent_config.to_formkit_form(),
            agent_config_specs=AgentConfigSpecs.from_agent_config(self.agent_config, self.agent_class),
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
            self.topic_manager, thread_id=topic.thread_id, display_id=topic.display_id, run_id=topic.run_id
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
        3. Start the parent BotsTestRunner's run method to launch the server.

        Requires that at least one simulated event is provided; otherwise, it's a no-op.
        """
        assert len(self.simulated_events) > 0, "No simulated events provided"

        self.nc = await NatsSettings.create_client()

        self.nc_publisher = NCPublisher(f"Simulated{self.agent_class}BotTestRunnerDiscoveryResponse", self.nc)
        self.discovery_subscriber = AgentNCSubscriber.for_agent_class_discovery_request_events(
            self.nc,
            AgentTopicManager(),
            self.discovery_handler,
            subscriber_name=f"Simulated{self.agent_class}BotTestRunnerDiscoveryRequest",
        )
        await self.discovery_subscriber.start()

        self.js = self.nc.jetstream()
        self.agent_control_event_subscriber = AgentJSSubscriber.for_agent_instance_control_events(
            self.nc,
            self.topic_manager,
            js=self.js,
            handler=self.simulate_agent,
            queue_group="simulated-agent-bot-runner-queue-group",
            subscriber_name=f"Simulated{self.agent_class}BotTestRunnerControlEvents",
        )
        await self.agent_control_event_subscriber.start()

        self.js_publisher = JSPublisher(f"Simulated{self.agent_class}BotTestRunner", self.js)

    async def run(self):
        await self.start_simulation()
        await super().run()

    def with_simple_chunk_events(self) -> Self:
        """
        A convenience method to populate a standard sequence of chunk and cost events, simulating
        a typical LLM-based agent responding with textual chunks and cost metrics.

        This returns `self` so it can be chained:
        ```python
        runner = SimulatedAgentBotsTestRunner("my_class", "my_id").with_simple_chunk_events()
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
            ChunkEvent(content="Second chunk.", model_name=model_name),
            LLMCostEvent(
                llm_name=model_name,
                prompt_token_count=7,
                completion_token_count=16,
                embedding_token_count=0,
                prompt_tokens_costs=0.1,
                completion_tokens_costs=0.3,
                embedding_tokens_costs=0.05,
            ),
        ]
        return self
