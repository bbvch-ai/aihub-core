from typing import Annotated, Optional

from pydantic import BaseModel, Field


class EventPayloadField(BaseModel):
    """Information about an event payload field."""
    type: Annotated[str, Field(description="The human-readable type of the payload field")]
    description: Annotated[Optional[str], Field(description="Description of the payload field, if available")]