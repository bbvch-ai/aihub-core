from typing import Annotated, Optional, List

from aihub_api.auth.identity.UserIdentity import UserIdentity
from aihub_lib.auth.AuthenticatedUser import AuthenticatedUser
from pydantic import BaseModel, Field

from aihub_lib.persistence.user.UserEntity import UserEntity


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

    @classmethod
    def from_user_entity(cls, user_entity: UserEntity):
        return cls(
            id=user_entity.id,
            name=user_entity.name,
            email=user_entity.email,
            profile_image=user_entity.profile_image
        )

    @classmethod
    def from_user_identity(cls, user_identity: UserIdentity):
        return cls(
            id=user_identity.id,
            name=user_identity.name,
            email=user_identity.email,
            profile_image=user_identity.profile_image
        )