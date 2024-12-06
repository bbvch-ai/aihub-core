from typing import Dict, Optional

from pydantic import BaseModel, Field

from lib_core.nats.topic_managers.TopicManager import TopicManager
from lib_core.persistence.messaging.entities.PersistedEventEntity import PersistedEventEntity


class WSServerEvent(BaseModel):
    agent_class: str
    agent_id: str
    thread_id: str
    display_id: str
    run_id: Optional[str]
    event_type: Optional[str] = Field(TopicManager.DISPLAY_EVENT)
    event_name: str
    event_data: Dict

    @classmethod
    def from_persisted_event(cls, persisted_event: PersistedEventEntity):
        return cls(
            agent_class=persisted_event.agent_class,
            agent_id=persisted_event.agent_id,
            thread_id=persisted_event.thread_id,
            display_id=persisted_event.display_id,
            run_id=persisted_event.run_id,
            event_type=persisted_event.event_type,
            event_name=persisted_event.event_name,
            event_data=persisted_event.event_data,
        )