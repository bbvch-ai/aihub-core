import copy
from typing import Annotated, Any

from pydantic import BaseModel, Field

from swiss_ai_hub.core.events.base_event import BaseEvent


class EventSpecs(BaseModel):
    """
    Defines the schema of an event that can flow through NATs that is either produced or consumed by an agent
    or agentic process.

    Sometimes, we must communicate events to external consumers that do not have access to our internal Pydantic event
    model. Hence, we must serialize the model schema, add the event name and parent event names, and provide
    these information to an external consumer like an API endpoint or the frontend.

    From this information, we can reconstruct the pydantic object and send the event back into NATs such that
    it can be consumed by the agent as a native pydantic model again.
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
            event_schema=copy.deepcopy(event_class.model_json_schema()),
            event_parents=event_class.parent_event_names_from_class(),
        )
