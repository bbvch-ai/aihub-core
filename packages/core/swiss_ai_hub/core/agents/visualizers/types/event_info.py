from typing import Annotated

from pydantic import BaseModel, Field

from swiss_ai_hub.core.agents.visualizers.types.event_payload_field import EventPayloadField


class EventInfo(BaseModel):
    """Information about an event."""

    name: Annotated[str, Field(description="The name of the event class")]
    full_name: Annotated[str, Field(description="The fully qualified name of the event class")]
    is_start_event: Annotated[bool, Field(description="Whether this is a start event")]
    is_stop_event: Annotated[bool, Field(description="Whether this is a stop event")]
    payload: Annotated[dict[str, EventPayloadField], Field(description="Information about the event payload fields")]
