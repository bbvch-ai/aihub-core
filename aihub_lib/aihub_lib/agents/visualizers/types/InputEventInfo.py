from typing import Annotated, List

from pydantic import BaseModel, Field

from aihub_lib.agents.visualizers.types.EventInfo import EventInfo


class InputEventInfo(BaseModel):
    """Information about an input event for a step."""
    event_types: Annotated[List[EventInfo], Field(description="The types of events that can be accepted")]
    optional: Annotated[bool, Field(description="Whether this input is optional")]