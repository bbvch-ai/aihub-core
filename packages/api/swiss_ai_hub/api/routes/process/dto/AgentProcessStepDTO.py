from typing import TYPE_CHECKING, Annotated, Literal, Self

from pydantic import Field

from swiss_ai_hub.api.routes.process.dto.AgentWorkRequestDTO import AgentWorkRequestDTO
from swiss_ai_hub.api.routes.process.dto.AgentWorkResponseDTO import AgentWorkResponseDTO
from swiss_ai_hub.api.routes.process.dto.BaseProcessStepDTO import BaseProcessStepDTO
from swiss_ai_hub.api.routes.process.dto.PersistedEventDTO import PersistedEventDTO

if TYPE_CHECKING:
    from swiss_ai_hub.core.i18n.LocaleHandler import LocaleHandler


class AgentProcessStepDTO(BaseProcessStepDTO):
    """DTO representing an agent process step with agent-specific work request and response information."""

    step_type: Annotated[Literal["agent"], Field(description="Type of entity involved in this step.")] = "agent"
    work_request: Annotated[AgentWorkRequestDTO | None, Field(description="The agent work request for this step.")] = (
        None
    )
    work_response: Annotated[
        AgentWorkResponseDTO | None,
        Field(description="The agent work response for this step. May be None if work is not yet completed."),
    ] = None

    @classmethod
    def from_events(
        cls,
        request_event,
        response_event,
        step_index: int,
        t: "LocaleHandler",
    ) -> Self:
        """Creates an AgentProcessStepDTO from optional request and response events."""
        work_request: AgentWorkRequestDTO | None = None
        if request_event:
            if isinstance(request_event, dict):
                request_event = PersistedEventDTO.model_validate(request_event)
            work_request = AgentWorkRequestDTO.from_event_data(
                request_event.event_data,
                request_event.event_id,
                request_event.event_name,
                request_event.event_data["created_at"],
                t,
            )

        work_response: AgentWorkResponseDTO | None = None
        created_at = 0
        if response_event:
            if isinstance(response_event, dict):
                response_event = PersistedEventDTO.model_validate(response_event)
            work_response = AgentWorkResponseDTO.from_event_data(
                response_event.event_data,
                response_event.event_id,
                response_event.event_name,
                response_event.event_data["created_at"],
                t,
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
