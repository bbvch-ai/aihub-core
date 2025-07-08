from typing import Annotated

from aihub_lib.persistence.user.UserEntity import UserEntity
from pydantic import BaseModel, Field


class MinimalUserDTO(BaseModel):
    id: Annotated[str, Field(description="The user's unique identifier (OID).")]
    name: Annotated[str, Field(description="The user's name.")]
    email: Annotated[str, Field(description="The user's email address.")]
    profile_image: Annotated[str | None, Field(description="User's profile image in base64.")] = None

    @classmethod
    def from_user_entity(cls, user_entity: UserEntity):
        return cls(
            id=user_entity.id, name=user_entity.name, email=user_entity.email, profile_image=user_entity.profile_image
        )
