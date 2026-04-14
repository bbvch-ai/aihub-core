from typing import Annotated, Self

from pydantic import BaseModel, Field
from swiss_ai_hub.core.auth.keycloak.models.keycloak_user import KeycloakUser


class MinimalUserDTO(BaseModel):
    id: Annotated[str, Field(description="The user's unique identifier (OID).")]
    name: Annotated[str, Field(description="The user's name.")]
    email: Annotated[str, Field(description="The user's email address.")]
    profile_image: Annotated[str | None, Field(description="User's profile image in base64.")] = None

    @classmethod
    def from_keycloak_user(cls, user: KeycloakUser) -> Self:
        return cls(
            id=user.id,
            name=user.name,
            email=user.email,
            profile_image=None,
        )
