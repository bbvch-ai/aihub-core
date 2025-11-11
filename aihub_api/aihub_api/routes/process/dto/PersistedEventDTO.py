from typing import Annotated, Any

from pydantic import BaseModel, Field


class PersistedEventDTO(BaseModel):
    """DTO representing a persisted process event from MongoDB."""

    event_id: Annotated[str, Field(description="Unique identifier of the event.")]
    event_type: Annotated[str, Field(description="Type of the event (work, work_request, etc.).")]
    event_name: Annotated[str, Field(description="Name of the specific event.")]
    event_data: Annotated[dict[str, Any], Field(description="The event data payload.")]
    event_parents: Annotated[list[str], Field(description="List of parent event types.")]
    process_class: Annotated[str, Field(description="The process class this event belongs to.")]
    process_id: Annotated[str, Field(description="The process ID this event belongs to.")]
    process_walkthrough_id: Annotated[str, Field(description="The walkthrough ID this event belongs to.")]
