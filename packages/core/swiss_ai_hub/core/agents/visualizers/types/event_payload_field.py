from typing import Annotated

from pydantic import BaseModel, Field


class EventPayloadField(BaseModel):
    """Information about an event payload field."""

    type: Annotated[str, Field(description="The human-readable type of the payload field")]
    description: Annotated[str | None, Field(description="Description of the payload field, if available")]
