from typing import Annotated

from pydantic import BaseModel, Field

from aihub_api.routes.agent.dto.MinimalAgentDTO import MinimalAgentDTO
from aihub_api.routes.user.dto.MinimalUserDTO import MinimalUserDTO


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

    is_active: Annotated[bool, Field(description="Whether this walkthrough is active (no ProcessStopEvent).")]

    involved_agents: Annotated[list[MinimalAgentDTO], Field(description="List of agents that submitted work in this walkthrough.")]

    involved_humans: Annotated[list[MinimalUserDTO], Field(description="List of humans that submitted work in this walkthrough.")]


# Rebuild model to resolve forward references
try:
    ProcessWalkthroughDTO.model_rebuild()
except Exception:
    pass  # Ignore if already rebuilt
