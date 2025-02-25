from typing import Annotated, Optional

from aihub_lib.auth.AuthenticatedUser import AuthenticatedUser
from pydantic import BaseModel, Field


class UserDTO(BaseModel):
    id: Annotated[str, Field(description="The user's unique identifier (OID).")]
    name: Annotated[str, Field(description="The user's name.")]
    email: Annotated[str, Field(description="The user's email address.")]
    profile_image: Annotated[Optional[str], Field(description="User's profile image in base64.")] = None

    @classmethod
    def from_authenticated_user(cls, user: AuthenticatedUser):
        return cls(
            id=user.oid,
            name=user.name,
            email=user.preferred_username,
        )
