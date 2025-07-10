from typing import Annotated, Any

from pydantic import BaseModel, Field

from aihub_lib.nats.events import BaseEvent


class EventSpecs(BaseModel):
    """
    Defines a specification for a start event that an agent can handle.
    """

    event_name: Annotated[
        str,
        Field(
            description="The name of event (e.g., a particular ControlEvent subclass name) "
            "that the agent can consume as a start event.",
        ),
    ]
    event_schema: Annotated[
        dict[str, Any],
        Field(
            description="A dictionary describing the schema of this start event, providing details about "
            "expected fields and their types. This helps external consumers understand how to "
            "construct and validate events for initiating the agent's workflow.",
        ),
    ]
    event_parents: Annotated[
        list[str],
        Field(
            description="A list of parent event names that this event is derived from, "
            "allowing for hierarchical event structures."
        ),
    ]

    @classmethod
    def from_event_class(cls, event_class: type[BaseEvent]):
        return cls(
            event_name=event_class.event_name_from_class(),
            event_schema=event_class.model_json_schema(),
            event_parents=event_class.parent_event_names_from_class(),
        )
