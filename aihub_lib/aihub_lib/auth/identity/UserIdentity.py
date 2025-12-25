from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from aihub_lib.persistence.user.UserEntity import UserEntity


class UserIdentity(BaseModel):
    """
    Lightweight identity object for authenticated users.

    Used in authentication handlers and API responses. This is a DTO (Data Transfer Object)
    that represents the authenticated user's identity without database dependencies.
    """

    id: Annotated[str, Field(description="The unique identifier for the user.")]
    name: Annotated[str, Field(description="The name of the user.")]
    email: Annotated[str, Field(description="The email address of the user.")]
    roles: Annotated[list[str], Field(description="The roles assigned to the user.")]
    profile_image: Annotated[str | None, Field(description="Data URL (base64) representation of profile image")] = None

    @classmethod
    def from_user_entity(cls, user: UserEntity) -> UserIdentity:
        """Create a UserIdentity from a UserEntity database object."""
        return cls(
            id=user.id,
            name=user.name,
            email=user.email,
            roles=user.roles,
            profile_image=user.profile_image,
        )
