from typing import TYPE_CHECKING, Annotated, Any, Self

from pydantic import Field

from .WorkRequestDTO import WorkRequestDTO

if TYPE_CHECKING:
    from swiss_ai_hub.core.i18n.LocaleHandler import LocaleHandler


class HumanWorkRequestDTO(WorkRequestDTO):
    """DTO representing a human work request with specific human-related information."""

    user_ids: Annotated[list[str], Field(description="List of user IDs that can respond to this request.")] = []
    user_emails: Annotated[list[str], Field(description="List of user emails that can respond to this request.")] = []
    user_roles: Annotated[list[str], Field(description="List of user roles that can respond to this request.")] = []
    notify: Annotated[bool, Field(description="Whether users should be notified about this request.")] = False
    forms: Annotated[list[dict[str, Any]], Field(description="List of forms that users can submit.")] = []
    endpoint: Annotated[str | None, Field(description="API endpoint for form submission.")] = None
    method: Annotated[str | None, Field(description="HTTP method for form submission.")] = None

    @classmethod
    def from_event_data(
        cls, event_data: dict, event_id: str, event_name: str, created_at: int, t: "LocaleHandler"
    ) -> Self:
        """Creates a HumanWorkRequestDTO from raw event data."""
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
            request_type="human",
            display_name=display_name,
            display_description=display_description,
            data=event_data,
            user_ids=event_data.get("user_ids", []),
            user_emails=event_data.get("user_emails", []),
            user_roles=event_data.get("user_roles", []),
            notify=event_data.get("notify", False),
            forms=event_data.get("forms", []),
            endpoint=event_data.get("endpoint"),
            method=event_data.get("method"),
        )
