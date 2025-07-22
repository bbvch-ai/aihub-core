from typing import Annotated

from pydantic import BaseModel, Field


class ProcessWalkthroughDTO(BaseModel):
    """DTO representing a process walkthrough with detailed step information."""

    process_walkthrough_id: Annotated[
        str, Field(description="Unique identifier for this specific process walkthrough.")
    ]

    process_class: Annotated[str, Field(description="The class/type of the process.")]

    process_id: Annotated[str, Field(description="Unique identifier for the specific process instance.")]

    process_steps: Annotated[list, Field(description="List of all steps in this walkthrough, ordered chronologically.")]

    created_at: Annotated[int, Field(description="Timestamp of the first event in nanoseconds.")]

    updated_at: Annotated[int, Field(description="Timestamp of the last event in nanoseconds.")]

    total_steps: Annotated[int, Field(description="Total number of steps in this walkthrough.")]

    completed_steps: Annotated[int, Field(description="Number of completed steps in this walkthrough.")]

    is_active: Annotated[bool, Field(description="Whether this walkthrough has uncompleted steps.")]
