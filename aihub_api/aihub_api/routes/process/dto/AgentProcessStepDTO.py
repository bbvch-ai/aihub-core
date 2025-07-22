from typing import TYPE_CHECKING, Annotated

from pydantic import Field

from .AgentWorkRequestDTO import AgentWorkRequestDTO
from .AgentWorkResponseDTO import AgentWorkResponseDTO
from .BaseProcessStepDTO import BaseProcessStepDTO

if TYPE_CHECKING:
    from aihub_lib.i18n.LocaleHandler import LocaleHandler


class AgentProcessStepDTO(BaseProcessStepDTO):
    """DTO representing an agent process step with agent-specific work request and response information."""

    step_type: Annotated[str, Field(default="agent", description="Type of entity involved in this step.")]

    work_request: Annotated[
        AgentWorkRequestDTO | None,
        Field(description="The agent work request for this step."),
    ]

    work_response: Annotated[
        AgentWorkResponseDTO | None,
        Field(description="The agent work response for this step. May be None if work is not yet completed."),
    ]

    @classmethod
    def from_events(cls, request_event: "PersistedEventDTO | None", response_event: "PersistedEventDTO | None", step_index: int, t: "LocaleHandler") -> "AgentProcessStepDTO":
        """Creates an AgentProcessStepDTO from optional request and response events."""
        from .PersistedEventDTO import PersistedEventDTO

        # Create work request if request_event exists
        work_request = None
        agent_info = None
        if request_event:
            # Convert dict to PersistedEventDTO for better typing
            if isinstance(request_event, dict):
                request_event = PersistedEventDTO(**request_event)

            request_data = request_event.event_data
            work_request = AgentWorkRequestDTO.from_event_data(
                request_data,
                request_event.event_id,
                request_event.event_name,
                request_data.get("created_at", 0),
                t,
            )
            agent_info = work_request.agent_info

        # Create work response if exists
        work_response = None
        created_at = 0
        if response_event:
            if isinstance(response_event, dict):
                response_event = PersistedEventDTO(**response_event)
            response_data = response_event.event_data
            work_response = AgentWorkResponseDTO.from_event_data(
                response_data,
                response_event.event_id,
                response_event.event_name,
                response_data.get("created_at", 0),
                t,
                agent_info,  # Pass agent_info from request (may be None)
            )
            created_at = work_response.created_at

        # Use request creation time if available, otherwise response creation time
        if work_request:
            created_at = work_request.created_at

        return cls(
            step_index=step_index,
            created_at=created_at,
            is_completed=work_response is not None,
            work_request=work_request,
            work_response=work_response,
        )


# Rebuild model to resolve forward references
try:
    AgentProcessStepDTO.model_rebuild()
except Exception:
    pass  # Ignore if already rebuilt
