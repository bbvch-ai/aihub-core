import json
from typing import Self

from mongoengine import EmbeddedDocument, ListField, StringField

from swiss_ai_hub.core.events.discovery.event_specs import EventSpecs


class EventSpecEntity(EmbeddedDocument):
    """An announced event specification, embedded in the process classes that stay on MongoEngine."""

    event_name = StringField(required=True)
    event_schema_json = StringField(required=True)  # Store as JSON string to avoid issues with $ in keys
    event_parents = ListField(StringField(), default=list)

    @property
    def event_schema(self):
        """Deserialize the event schema from JSON string to dictionary."""
        return json.loads(self.event_schema_json)

    @classmethod
    def from_specs(cls, event_specs: EventSpecs) -> Self:
        """Create an EventSpecEntity from an EventSpecs object."""
        return cls(
            event_name=event_specs.event_name,
            event_schema_json=json.dumps(event_specs.event_schema),
            event_parents=event_specs.event_parents,
        )

    def to_specs(self) -> EventSpecs:
        """Convert this entity back to an EventSpecs Pydantic model."""
        return EventSpecs(
            event_name=self.event_name,
            event_schema=self.event_schema,
            event_parents=self.event_parents,
        )
