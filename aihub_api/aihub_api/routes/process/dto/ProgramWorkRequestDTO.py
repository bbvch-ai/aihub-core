from typing import TYPE_CHECKING, Annotated, Self

from pydantic import Field

from .WorkRequestDTO import WorkRequestDTO

if TYPE_CHECKING:
    from aihub_lib.i18n.LocaleHandler import LocaleHandler


class ProgramWorkRequestDTO(WorkRequestDTO):
    """DTO representing a program work request with specific program-related information."""

    endpoint: Annotated[str | None, Field(description="API endpoint for the program to submit work.")] = None
    method: Annotated[str | None, Field(description="HTTP method for the program to submit work.")] = None

    @classmethod
    def from_event_data(
        cls, event_data: dict, event_id: str, event_name: str, created_at: int, t: "LocaleHandler"
    ) -> Self:
        """Creates a ProgramWorkRequestDTO from raw event data."""
        display_name: str | None = None
        display_description: str | None = None
        if event_data.get("display_name"):
            display_name = t.extract(event_data["display_name"])
        if event_data.get("display_description"):
            display_description = t.extract(event_data["display_description"])

        return cls(
            event_id=event_id,
            event_name=event_name,
            created_at=created_at,
            request_type="program",
            display_name=display_name,
            display_description=display_description,
            data=event_data,
            endpoint=event_data.get("endpoint"),
            method=event_data.get("method"),
        )
