from nats.aio.client import Client as NATS
from nats.js import JetStreamContext

from api_core.runners.ApiTestRunner import ApiTestRuner
from lib_core.nats.events import ControlEvent, StartEvent, BaseEvent, StopEvent, ChunkEvent, DisplayEvent
from lib_core.nats.events.cost.LLMCostEvent import LLMCostEvent
from lib_core.nats.publishers.JSPublisher import JSPublisher
from lib_core.nats.subscribers.JSSubscriber import JSSubscriber
from lib_core.nats.topic_managers.agents.AgentInstanceTopicManager import AgentInstanceTopicManager
from lib_core.nats.topic_managers.agents.AgentThreadTopicManager import AgentThreadTopicManager
from lib_core.nats.topics.agents.AgentTopic import AgentTopic


class SimulatedAgentApiTestRunner(ApiTestRuner):

    def __init__(self, agent_class: str, agent_id: str):
        super().__init__()
        self.agent_class = agent_class
        self.agent_id = agent_id
        self.topic_manager = AgentInstanceTopicManager(agent_class, agent_id)

        self.nc: NATS | None = None
        self.js: JetStreamContext | None = None

        self.subscriber: JSSubscriber[ControlEvent] | None = None
        self.publisher: JSPublisher | None = None


    async def simulate_agent(self, event: ControlEvent, topic: AgentTopic):
        model_name = "gpt-4"
        if isinstance(event, StartEvent):
            await self.publish_event(ChunkEvent(content="First chunk.\n", model_name=model_name), topic)
            await self.publish_event(LLMCostEvent(
                llm_name=model_name,
                prompt_token_count=9,
                completion_token_count=15,
                embedding_token_count=0,
                prompt_tokens_costs=0.1,
                completion_tokens_costs=0.3,
                embedding_tokens_costs=0.05,
            ), topic)
            await self.publish_event(ChunkEvent(content="Second chunk", model_name=model_name), topic)
            await self.publish_event(LLMCostEvent(
                llm_name=model_name,
                prompt_token_count=7,
                completion_token_count=16,
                embedding_token_count=0,
                prompt_tokens_costs=0.1,
                completion_tokens_costs=0.3,
                embedding_tokens_costs=0.05,
            ), topic)
            await self.publish_event(StopEvent(), topic)

    async def publish_event(self, event: BaseEvent, topic: AgentTopic):
        thread_topic_manager = AgentThreadTopicManager.from_agent_instance_topic_manager(
            self.topic_manager,
            thread_id=topic.thread_id,
            display_id=topic.display_id,
            run_id=topic.run_id
        )
        if isinstance(event, ControlEvent):
            subject = thread_topic_manager.get_subject_for_control_event_in_thread(event.__class__.__name__, event.event_id)
            await self.publisher.publish_event(event, subject)
        if isinstance(event, DisplayEvent):
            subject = thread_topic_manager.get_subject_for_display_event_in_thread(event.__class__.__name__,
                                                                                   event.event_id)
            await self.publisher.publish_event(event, subject)

    async def run(self):
        self.nc = NATS()
        await self.nc.connect(servers=["nats://localhost:4222"])

        self.js = self.nc.jetstream()
        self.subscriber = JSSubscriber.for_agent_instance_control_events(
            self.nc,
            self.topic_manager,
            js=self.js,
            handler=self.simulate_agent,
        )
        self.publisher = JSPublisher(self.js)
        await self.subscriber.start()

        await super().run()