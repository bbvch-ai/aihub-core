from typing import TYPE_CHECKING, Annotated, Self

from pydantic import Field

from aihub_api.routes.user.dto.MinimalUserDTO import MinimalUserDTO

from .WorkResponseDTO import WorkResponseDTO

if TYPE_CHECKING:
    from aihub_lib.i18n.LocaleHandler import LocaleHandler


class ProgramWorkResponseDTO(WorkResponseDTO):
    """DTO representing a program work response with specific program-related information."""

    submitted_by: Annotated[
        MinimalUserDTO | None, Field(description="The user who submitted this work response on behalf of the program.")
    ] = None

    @classmethod
    def from_event_data(
        cls, event_data: dict, event_id: str, event_name: str, created_at: int, t: "LocaleHandler"
    ) -> Self:
        """Creates a ProgramWorkResponseDTO from raw event data."""
        from aihub_lib.persistence.user.UserEntity import UserEntity

        from aihub_api.routes.user.dto.MinimalUserDTO import MinimalUserDTO

        display_name: str | None = None
        display_description: str | None = None
        if event_data.get("display_name"):
            display_name = t.extract(event_data["display_name"])
        if event_data.get("display_description"):
            display_description = t.extract(event_data["display_description"])

        submitted_by_data = event_data.get("submitted_by")
        submitted_by: MinimalUserDTO | None = None

        if submitted_by_data:
            user_id = (
                submitted_by_data.get("id")
                if isinstance(submitted_by_data, dict)
                else getattr(submitted_by_data, "id", None)
            )
            profile_image = (
                submitted_by_data.get("profile_image")
                if isinstance(submitted_by_data, dict)
                else getattr(submitted_by_data, "profile_image", None)
            )

            if not profile_image and user_id:
                try:
                    user_entity = UserEntity.by_oid(user_id)
                    submitted_by = MinimalUserDTO.from_user_entity(user_entity)
                except Exception:
                    pass

            if not submitted_by:
                submitted_by = MinimalUserDTO.model_validate(
                    {
                        "id": user_id or "",
                        "name": submitted_by_data.get("name")
                        if isinstance(submitted_by_data, dict)
                        else getattr(submitted_by_data, "name", ""),
                        "email": submitted_by_data.get("email")
                        if isinstance(submitted_by_data, dict)
                        else getattr(submitted_by_data, "email", ""),
                        "profile_image": profile_image,
                    }
                )

        return cls(
            event_id=event_id,
            event_name=event_name,
            created_at=created_at,
            response_type="program",
            display_name=display_name,
            display_description=display_description,
            data=event_data,
            submitted_by=submitted_by,
        )
