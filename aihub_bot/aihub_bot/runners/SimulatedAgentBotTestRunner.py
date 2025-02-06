import logging
from typing import List, Optional

from nats.aio.client import Client as NATS
from nats.js import JetStreamContext

from aihub_bot.runners.BotTestRunner import BotTestRunner
from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events import BaseEvent, ChunkEvent, ControlEvent, DisplayEvent, StartEvent, StopEvent
from aihub_lib.nats.events.cost.LLMCostEvent import LLMCostEvent
from aihub_lib.nats.events.discovery.AgentDiscoveryResponseEvent import AgentDiscoveryResponseEvent, StartEventSpecs
from aihub_lib.nats.events.discovery.DiscoveryRequestEvent import DiscoveryRequestEvent
from aihub_lib.nats.publishers.JSPublisher import JSPublisher
from aihub_lib.nats.publishers.NCPublisher import NCPublisher
from aihub_lib.nats.subscribers.JSSubscriber import JSSubscriber
from aihub_lib.nats.subscribers.NCSubscriber import NCSubscriber
from aihub_lib.nats.topic_managers.TopicManager import TopicManager
from aihub_lib.nats.topic_managers.agents.AgentInstanceTopicManager import AgentInstanceTopicManager
from aihub_lib.nats.topic_managers.agents.AgentThreadTopicManager import AgentThreadTopicManager
from aihub_lib.nats.topics import DiscoveryTopic
from aihub_lib.nats.topics.agents.AgentTopic import AgentTopic

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
        simulated_events: Optional[List[BaseEvent]] = None,
    ):
        super().__init__()
        self.agent_class = agent_class
        self.agent_id = agent_id
        self.topic_manager = AgentInstanceTopicManager(agent_class, agent_id)

        self.nc: Optional[NATS] = None
        self.js: Optional[JetStreamContext] = None

        self.agent_control_event_subscriber: Optional[JSSubscriber[ControlEvent]] = None
        self.js_publisher: Optional[JSPublisher] = None

        self.nc_publisher: Optional[NCPublisher[AgentDiscoveryResponseEvent]] = None
        self.discovery_subscriber: Optional[NCSubscriber[DiscoveryRequestEvent]] = None

        self.simulated_events: List[BaseEvent] = simulated_events or []

    async def simulate_agent(self, event: ControlEvent, topic: AgentTopic):
        """
        Handler for control events targeting this agent instance. If a StartEvent arrives,
        publish the simulated events in sequence, followed by a StopEvent to conclude the run.

        This simulates an agent run, where after receiving a start signal, the agent responds
        with chunks, cost events, etc., and finally a stop signal.
        """
        if isinstance(event, StartEvent):
            for sim_event in self.simulated_events:
                await self.publish_event(sim_event, topic)
            await self.publish_event(StopEvent(), topic)

    async def discovery_handler(self, event: DiscoveryRequestEvent, topic: DiscoveryTopic):
        """
        Responds to a discovery request by publishing an `AgentDiscoveryResponseEvent`.
        This simulates the agent being discoverable by clients, providing metadata and start events.
        """
        subject = self.topic_manager.get_agent_discovery_subject_response(topic.call_id)
        start_events = [StartEventSpecs(event_type=StartEvent.__name__, event_schema=StartEvent.model_json_schema())]
        agent_discovery_response_event = AgentDiscoveryResponseEvent(
            agent_class=self.agent_class,
            agent_id=self.agent_id,
            agent_config=AgentConfig(
                agent_id=self.agent_id,
                name=LocaleString(de="Test Agent"),
                description=LocaleString(de="Test Agent Description"),
                system_prompt=LocaleString(de="Test Agent System Prompt"),
            ),
            start_events=start_events,
        )
        await self.nc_publisher.publish_event(agent_discovery_response_event, subject)

    async def publish_event(self, event: BaseEvent, topic: AgentTopic):
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
        if isinstance(event, ControlEvent):
            subject = thread_topic_manager.get_subject_for_control_event_in_thread(
                event.__class__.__name__, event.event_id
            )
            logger.debug(f"Publishing control event {event.__class__.__name__} to {subject}")
            await self.js_publisher.publish_event(event, subject)

        if isinstance(event, DisplayEvent):
            subject = thread_topic_manager.get_subject_for_display_event_in_thread(
                event.__class__.__name__, event.event_id
            )
            logger.debug(f"Publishing display event {event.__class__.__name__} to {subject}")
            await self.js_publisher.publish_event(event, subject)

    async def run(self):
        """
        Orchestrates the simulation:
        1. Connect to NATS.
        2. Set up publishers and subscribers (discovery requests, agent control events).
        3. Start the parent BotsTestRunner's run method to launch the server.

        Requires that at least one simulated event is provided; otherwise, it's a no-op.
        """
        assert len(self.simulated_events) > 0, "No simulated events provided"

        self.nc = NATS()
        await self.nc.connect(servers=["nats://localhost:4222"])

        self.nc_publisher = NCPublisher(self.nc)
        self.discovery_subscriber = NCSubscriber.for_agent_discovery_request_events(
            self.nc, TopicManager(), self.discovery_handler
        )
        await self.discovery_subscriber.start()

        self.js = self.nc.jetstream()
        self.agent_control_event_subscriber = JSSubscriber.for_agent_instance_control_events(
            self.nc,
            self.topic_manager,
            js=self.js,
            handler=self.simulate_agent,
        )
        await self.agent_control_event_subscriber.start()

        self.js_publisher = JSPublisher(self.js)

        await super().run()

    def with_simple_chunk_events(self) -> "SimulatedAgentBotTestRunner":
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
