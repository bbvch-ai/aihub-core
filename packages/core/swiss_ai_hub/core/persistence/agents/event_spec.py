import json
from typing import Any, Self

from pydantic import BaseModel, ConfigDict, Field

from swiss_ai_hub.core.events.discovery.event_specs import EventSpecs


class EventSpec(BaseModel):
    """An announced event specification, embedded in `AgentClassEntity`.

    The schema is stored as a JSON string because MongoDB rejects dictionary keys starting with '$'.
    """

    model_config = ConfigDict(extra="allow")

    event_name: str
    event_schema_json: str
    event_parents: list[str] = Field(default_factory=list)

    @property
    def event_schema(self) -> dict[str, Any]:
        return json.loads(self.event_schema_json)

    @classmethod
    def from_specs(cls, event_specs: EventSpecs) -> Self:
        return cls(
            event_name=event_specs.event_name,
            event_schema_json=json.dumps(event_specs.event_schema),
            event_parents=event_specs.event_parents,
        )

    def to_specs(self) -> EventSpecs:
        return EventSpecs(event_name=self.event_name, event_schema=self.event_schema, event_parents=self.event_parents)
