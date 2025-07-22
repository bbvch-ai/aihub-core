from typing import TYPE_CHECKING, Annotated

from aihub_lib.auth.identity.UserIdentity import UserIdentity
from pydantic import Field

from .WorkResponseDTO import WorkResponseDTO

if TYPE_CHECKING:
    from aihub_lib.i18n.LocaleHandler import LocaleHandler


class ProgramWorkResponseDTO(WorkResponseDTO):
    """DTO representing a program work response with specific program-related information."""

    submitted_by: Annotated[
        UserIdentity | None, Field(description="The user who submitted this work response on behalf of the program.")
    ]

    @classmethod
    def from_event_data(
        cls, event_data: dict, event_id: str, event_name: str, created_at: int, t: "LocaleHandler"
    ) -> "ProgramWorkResponseDTO":
        """Creates a ProgramWorkResponseDTO from raw event data."""
        # Extract localized display fields
        display_name = None
        display_description = None
        if event_data.get("display_name"):
            display_name = t.extract(event_data.get("display_name"))
        if event_data.get("display_description"):
            display_description = t.extract(event_data.get("display_description"))

        return cls(
            event_id=event_id,
            event_name=event_name,
            created_at=created_at,
            response_type="program",
            display_name=display_name,
            display_description=display_description,
            data=event_data,
            submitted_by=event_data.get("submitted_by"),
        )
