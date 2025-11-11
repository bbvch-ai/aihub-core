from typing import Annotated, Literal

from pydantic import BaseModel, Field


class BaseProcessStepDTO(BaseModel):
    """Base DTO representing a single step in a process walkthrough."""

    step_index: Annotated[int, Field(description="Order of this step in the walkthrough (0-based).")]
    step_type: Annotated[
        Literal["human", "agent", "program"], Field(description="Type of entity involved in this step.")
    ]
    created_at: Annotated[int, Field(description="Timestamp when this step was created in nanoseconds.")]
    is_completed: Annotated[bool, Field(description="Whether this step has been completed (has a work response).")]
