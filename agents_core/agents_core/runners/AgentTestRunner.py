import logging
from asyncio import sleep
from contextlib import asynccontextmanager
from typing import List, Type, AsyncGenerator

from bson import ObjectId
from openai import BaseModel

from agents_core.agents.abstract.Agent import Agent
from agents_core.agents.abstract.AgentConfig import AgentConfig
from agents_core.runners.AgentRunner import AgentRunner
from lib_core.nats.events import StartEvent, BaseEvent, StopEvent, ExceptionEvent
from lib_core.nats.subscribers.NCSubscriber import NCSubscriber
from lib_core.nats.topic_managers.agents.AgentThreadTopicManager import AgentThreadTopicManager
from lib_core.nats.topics.agents.AgentTopic import AgentTopic
from lib_core.nats.topics.agents.PartialAgentTopic import PartialAgentTopic



azure_loggers = [
    'azure.identity',
    'azure.core.pipeline',
    'azure.core.pipeline.policies',
    'azure.core.pipeline.transport',
    'urllib3'
]

for logger_name in azure_loggers:
    logging.getLogger(logger_name).setLevel(logging.WARNING)

class ObservedEvent(BaseModel):
    event: BaseEvent
    topic: AgentTopic

class AgentTestRunner(AgentRunner):

    def __init__(self, agent_class: Type[Agent], agent_config: AgentConfig):
        super().__init__(servers=["nats://localhost:4222"], agent_class=agent_class, agent_config=agent_config)
        self.observed_events = []

    async def send_event_from_topic(self, start_event: StartEvent, topic: PartialAgentTopic):
        await self.send_event(start_event, topic.thread_id, topic.display_id, topic.run_id)

    async def observe_event(self, event: BaseEvent, topic: AgentTopic):
        self.observed_events.append(ObservedEvent(event=event, topic=topic))

    @asynccontextmanager
    async def test_run(self, delay_before_stop: int = 1) -> AsyncGenerator[PartialAgentTopic, None]:
        await self.start()

        thread_id = str(ObjectId())
        display_id = str(ObjectId())
        run_id = str(ObjectId())

        event_subscriber = NCSubscriber.for_all_thread_events(
            nc=self.nc,
            topic_manager=AgentThreadTopicManager.from_agent_instance_topic_manager(
                self.topic_manager,
                thread_id=thread_id,
                display_id=display_id,
                run_id=run_id,
            ),
            handler=self.observe_event,
        )
        await event_subscriber.start()

        yield PartialAgentTopic(
            agent_class=self.agent_class.__name__,
            agent_id=self.agent_config.agent_id,
            run_id=run_id,
            thread_id=thread_id,
            display_id=display_id,
        )
        await sleep(delay_before_stop)
        await self.stop()

    @property
    def has_start_event(self) -> bool:
        return any(isinstance(event.event, StartEvent) for event in self.observed_events)

    @property
    def has_stop_event(self) -> bool:
        return any(isinstance(event.event, StopEvent) for event in self.observed_events)

    @property
    def has_exception_event(self) -> bool:
        return any(isinstance(event.event, ExceptionEvent) for event in self.observed_events)

    def get_events(self, event_type: Type[BaseEvent]) -> List[BaseEvent]:
        return [event.event for event in self.observed_events if isinstance(event.event, event_type)]

    def get_topics(self, event_type: Type[BaseEvent]) -> List[AgentTopic]:
        return [event.topic for event in self.observed_events if isinstance(event.event, event_type)]

    def get_events_of_type(self, event_type: Type[BaseEvent]) -> List[BaseEvent]:
        return [event.event for event in self.observed_events if isinstance(event.event, event_type)]

    def has_event_of_type(self, event_type: Type[BaseEvent]) -> bool:
        return any(isinstance(event.event, event_type) for event in self.observed_events)

    def get_event_of_type(self, event_type: Type[BaseEvent]) -> BaseEvent:
        return next(event.event for event in self.observed_events if isinstance(event.event, event_type))