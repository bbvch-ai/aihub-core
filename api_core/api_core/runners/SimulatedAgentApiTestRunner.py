import logging
from typing import List

from nats.aio.client import Client as NATS
from nats.js import JetStreamContext

from api_core.runners.ApiTestRunner import ApiTestRunner
from lib_core.generative_ai.agent.AgentConfig import AgentConfig
from lib_core.i18n.LocaleString import LocaleString
from lib_core.nats.events import ControlEvent, StartEvent, BaseEvent, StopEvent, ChunkEvent, DisplayEvent
from lib_core.nats.events.cost.LLMCostEvent import LLMCostEvent
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
from lib_core.nats.topics.agents.AgentTopic import AgentTopic

logger = logging.getLogger(__name__)

class SimulatedAgentApiTestRunner(ApiTestRunner):

    def __init__(self, agent_class: str, agent_id: str, simulated_events: List[BaseEvent] = None):
        super().__init__()
        self.agent_class = agent_class
        self.agent_id = agent_id
        self.topic_manager = AgentInstanceTopicManager(agent_class, agent_id)

        self.nc: NATS | None = None
        self.js: JetStreamContext | None = None

        self.agent_control_event_subscriber: JSSubscriber[ControlEvent] | None = None
        self.js_publisher: JSPublisher | None = None

        self.nc_publisher: NCPublisher[AgentDiscoveryResponseEvent] | None = None
        self.nc_publisher: NCPublisher[DiscoveryRequestEvent] | None = None

        self.simulated_events: List[BaseEvent] = simulated_events or []


    async def simulate_agent(self, event: ControlEvent, topic: AgentTopic):
        if isinstance(event, StartEvent):
            for event in self.simulated_events:
                await self.publish_event(event, topic)
            await self.publish_event(StopEvent(), topic)

    async def discovery_handler(self, event: DiscoveryRequestEvent, topic: DiscoveryTopic):
        subject = self.topic_manager.get_agent_discovery_subject_response(topic.call_id)
        start_events = [
            StartEventSpecs(event_type=StartEvent.__name__, event_schema=StartEvent.model_json_schema())
        ]
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
        thread_topic_manager = AgentThreadTopicManager.from_agent_instance_topic_manager(
            self.topic_manager,
            thread_id=topic.thread_id,
            display_id=topic.display_id,
            run_id=topic.run_id
        )
        if isinstance(event, ControlEvent):
            subject = thread_topic_manager.get_subject_for_control_event_in_thread(event.__class__.__name__, event.event_id)
            logger.debug(f"Publishing control event {event.__class__.__name__} to {subject}")
            await self.js_publisher.publish_event(event, subject)
        if isinstance(event, DisplayEvent):
            subject = thread_topic_manager.get_subject_for_display_event_in_thread(event.__class__.__name__,
                                                                                   event.event_id)
            logger.debug(f"Publishing display event {event.__class__.__name__} to {subject}")
            await self.js_publisher.publish_event(event, subject)

    async def run(self):
        assert len(self.simulated_events) > 0, "No simulated events provided"

        self.nc = NATS()
        await self.nc.connect(servers=["nats://localhost:4222"])

        self.nc_publisher = NCPublisher(self.nc)
        self.discovery_subscriber = NCSubscriber.for_agent_discovery_request_events(self.nc, TopicManager(), self.discovery_handler)
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

    def with_simple_chunk_events(self) -> 'SimulatedAgentApiTestRunner':
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
        ]
        return self