from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field


class WorkRequestDTO(BaseModel):
    """DTO representing a work request in a process step."""

    event_id: Annotated[str, Field(description="Unique identifier of the work request event.")]
    event_name: Annotated[str, Field(description="Name of the event type.")]
    created_at: Annotated[int, Field(description="Timestamp when the work was requested in nanoseconds.")]
    request_type: Annotated[
        Literal["human", "agent", "program"], Field(description="Type of entity the work was requested from.")
    ]
    display_name: Annotated[str | None, Field(description="Human-readable name for the work request.")]
    display_description: Annotated[str | None, Field(description="Human-readable description of the work request.")]
    data: Annotated[dict[str, Any], Field(description="The work request event data.")]
