from typing import TYPE_CHECKING, Annotated

from pydantic import Field

from aihub_api.routes.user.dto.MinimalUserDTO import MinimalUserDTO
from .WorkResponseDTO import WorkResponseDTO

if TYPE_CHECKING:
    from aihub_lib.i18n.LocaleHandler import LocaleHandler


class ProgramWorkResponseDTO(WorkResponseDTO):
    """DTO representing a program work response with specific program-related information."""

    submitted_by: Annotated[
        MinimalUserDTO | None, Field(description="The user who submitted this work response on behalf of the program.")
    ]

    @classmethod
    def from_event_data(
        cls, event_data: dict, event_id: str, event_name: str, created_at: int, t: "LocaleHandler"
    ) -> "ProgramWorkResponseDTO":
        """Creates a ProgramWorkResponseDTO from raw event data."""
        from aihub_lib.persistence.user.UserEntity import UserEntity
        from aihub_api.routes.user.dto.MinimalUserDTO import MinimalUserDTO
        
        # Extract localized display fields
        display_name = None
        display_description = None
        if event_data.get("display_name"):
            display_name = t.extract(event_data.get("display_name"))
        if event_data.get("display_description"):
            display_description = t.extract(event_data.get("display_description"))

        # Handle submitted_by user (may be None for programs)
        submitted_by_data = event_data.get("submitted_by")
        submitted_by = None
        
        if submitted_by_data:
            # Check if we need to fetch user profile
            profile_image = None
            user_id = None
            
            if isinstance(submitted_by_data, dict):
                profile_image = submitted_by_data.get("profile_image")
                user_id = submitted_by_data.get("id")
            else:
                profile_image = getattr(submitted_by_data, "profile_image", None)
                user_id = getattr(submitted_by_data, "id", None)
            
            if not profile_image and user_id:
                # Fetch user from database to get profile image
                try:
                    user_entity = UserEntity.get_user_by_id(user_id)
                    if user_entity:
                        submitted_by = MinimalUserDTO.from_user_entity(user_entity)
                except Exception:
                    pass  # User not found or error loading
            
            if not submitted_by and submitted_by_data:
                # Use existing user data
                if isinstance(submitted_by_data, dict):
                    submitted_by = MinimalUserDTO(
                        id=submitted_by_data.get("id", ""),
                        name=submitted_by_data.get("name", ""),
                        email=submitted_by_data.get("email", ""),
                        profile_image=profile_image
                    )
                else:
                    submitted_by = MinimalUserDTO(
                        id=getattr(submitted_by_data, "id", ""),
                        name=getattr(submitted_by_data, "name", ""),
                        email=getattr(submitted_by_data, "email", ""),
                        profile_image=profile_image
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


# Rebuild model to resolve forward references
try:
    ProgramWorkResponseDTO.model_rebuild()
except Exception:
    pass  # Ignore if already rebuilt
