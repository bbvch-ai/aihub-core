from typing import TYPE_CHECKING, Annotated, Literal, Self

from pydantic import Field

from .base_process_step_dto import BaseProcessStepDTO
from .program_work_request_dto import ProgramWorkRequestDTO
from .program_work_response_dto import ProgramWorkResponseDTO

if TYPE_CHECKING:
    from swiss_ai_hub.core.i18n import LocaleHandler


class ProgramProcessStepDTO(BaseProcessStepDTO):
    """DTO representing a program process step with program-specific work request and response information."""

    step_type: Annotated[Literal["program"], Field(description="Type of entity involved in this step.")] = "program"
    work_request: Annotated[
        ProgramWorkRequestDTO | None, Field(description="The program work request for this step.")
    ] = None
    work_response: Annotated[
        ProgramWorkResponseDTO | None,
        Field(description="The program work response for this step. May be None if work is not yet completed."),
    ] = None

    @classmethod
    def from_events(
        cls,
        request_event,
        response_event,
        step_index: int,
        t: "LocaleHandler",
    ) -> Self:
        """Creates a ProgramProcessStepDTO from optional request and response events."""
        from .persisted_event_dto import PersistedEventDTO

        work_request: ProgramWorkRequestDTO | None = None
        if request_event:
            if isinstance(request_event, dict):
                request_event = PersistedEventDTO.model_validate(request_event)
            work_request = ProgramWorkRequestDTO.from_event_data(
                request_event.event_data,
                request_event.event_id,
                request_event.event_name,
                request_event.event_data["created_at"],
                t,
            )

        work_response: ProgramWorkResponseDTO | None = None
        created_at = 0
        if response_event:
            if isinstance(response_event, dict):
                response_event = PersistedEventDTO.model_validate(response_event)
            work_response = ProgramWorkResponseDTO.from_event_data(
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
