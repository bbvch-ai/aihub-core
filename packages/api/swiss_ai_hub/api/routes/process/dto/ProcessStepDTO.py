from typing import Annotated, Literal

from pydantic import BaseModel, Field

from .WorkRequestDTO import WorkRequestDTO
from .WorkResponseDTO import WorkResponseDTO


class ProcessStepDTO(BaseModel):
    """DTO representing a single step in a process walkthrough."""

    step_index: Annotated[int, Field(description="Order of this step in the walkthrough (0-based).")]

    step_type: Annotated[
        Literal["human", "agent", "program"], Field(description="Type of entity involved in this step.")
    ]

    work_request: Annotated[
        WorkRequestDTO | None,
        Field(description="The work request for this step. Always present."),
    ]

    work_response: Annotated[
        WorkResponseDTO | None,
        Field(description="The work response for this step. May be None if work is not yet completed."),
    ]

    created_at: Annotated[int, Field(description="Timestamp when this step was created in nanoseconds.")]

    is_completed: Annotated[bool, Field(description="Whether this step has been completed (has a work response).")]
