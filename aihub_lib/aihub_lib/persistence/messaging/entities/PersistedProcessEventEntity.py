from typing import TYPE_CHECKING

from bson import ObjectId
from mongoengine import DictField, Document, ListField, StringField

if TYPE_CHECKING:
    from aihub_lib.nats.events import BaseEvent
    from aihub_lib.nats.topics import ProcessTopic


class PersistedProcessEventEntity(Document):
    meta = {
        "collection": "process_events",
        "strict": False,
    }
    process_class = StringField(required=True)
    process_id = StringField(required=True)
    process_walkthrough_id = StringField(required=True)
    event_id = StringField(required=True)
    event_type = StringField(required=True)
    event_name = StringField(required=True)
    event_data = DictField(required=True)
    event_parents = ListField(StringField(), required=True)

    @classmethod
    def persist_event(cls, event: "BaseEvent", topic: "ProcessTopic", db: str):
        persisted_entity = cls(
            id=ObjectId(),
            process_class=topic.agent_class,
            process_id=topic.agent_id,
            process_walkthrough_id=topic.thread_id,
            event_id=event.event_id,
            event_type=topic.event_type,
            event_name=topic.event_name,
            event_data=event.model_dump(),
            event_parents=event._parent_event_names,
        )
        persisted_entity.switch_db(db)
        persisted_entity.save()
