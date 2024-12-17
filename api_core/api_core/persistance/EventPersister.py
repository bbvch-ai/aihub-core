from bson import ObjectId

from lib_core.nats.events import BaseEvent
from lib_core.nats.topics.agents.AgentTopic import AgentTopic
from lib_core.persistence.messaging.entities.PersistedEventEntity import PersistedEventEntity


class EventPersister:

    def __init__(self, db: str):
        self.db = db

    async def persist_event(self, event: BaseEvent, topic: AgentTopic) -> None:
        event = PersistedEventEntity(
            id=ObjectId(),
            agent_class=topic.agent_class,
            agent_id=topic.agent_id,
            thread_id=topic.thread_id,
            display_id=topic.display_id,
            run_id=topic.run_id,
            event_id=event.event_id,
            event_type=topic.event_type,
            event_name=topic.event_name,
            event_data=event.model_dump(),
        )
        event.switch_db(self.db)
        event.save()
