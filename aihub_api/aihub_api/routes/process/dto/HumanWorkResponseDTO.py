from typing import TYPE_CHECKING, Annotated

from aihub_lib.auth.identity.UserIdentity import UserIdentity
from pydantic import Field

from .WorkResponseDTO import WorkResponseDTO

if TYPE_CHECKING:
    from aihub_lib.i18n.LocaleHandler import LocaleHandler


class HumanWorkResponseDTO(WorkResponseDTO):
    """DTO representing a human work response with specific human-related information."""

    submitted_by: Annotated[UserIdentity, Field(description="The user who submitted this work response.")]

    @classmethod
    def from_event_data(
        cls, event_data: dict, event_id: str, event_name: str, created_at: int, t: "LocaleHandler"
    ) -> "HumanWorkResponseDTO":
        """Creates a HumanWorkResponseDTO from raw event data."""
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
            response_type="human",
            display_name=display_name,
            display_description=display_description,
            data=event_data,
            submitted_by=event_data.get("submitted_by"),
        )
