from typing import Annotated

from pydantic import BaseModel, Field

from swiss_ai_hub.core.agents.visualizers.types.EventInfo import EventInfo


class InputEventInfo(BaseModel):
    """Information about an input event for a step."""

    event_names: Annotated[list[EventInfo], Field(description="The events that can be accepted")]
    optional: Annotated[bool, Field(description="Whether this input is optional")]
