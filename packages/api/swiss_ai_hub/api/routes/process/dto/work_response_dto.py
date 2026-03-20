from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field


class WorkResponseDTO(BaseModel):
    """DTO representing a work response in a process step."""

    event_id: Annotated[str, Field(description="Unique identifier of the work response event.")]
    event_name: Annotated[str, Field(description="Name of the event type.")]
    created_at: Annotated[int, Field(description="Timestamp when the work was completed in nanoseconds.")]
    response_type: Annotated[
        Literal["human", "agent", "program"], Field(description="Type of entity that completed the work.")
    ]
    display_name: Annotated[str | None, Field(description="Human-readable name for the work response.")]
    display_description: Annotated[str | None, Field(description="Human-readable description of the work response.")]
    data: Annotated[dict[str, Any], Field(description="The work response event data.")]
