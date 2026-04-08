from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, computed_field


class KeycloakUser(BaseModel):
    """Pydantic model for a Keycloak UserRepresentation."""

    model_config = ConfigDict(populate_by_name=True)

    id: Annotated[str, Field(description="Unique Keycloak user ID (UUID).")]
    username: Annotated[str, Field(description="Keycloak username.")] = ""
    first_name: Annotated[str | None, Field(alias="firstName", description="User's first name.")] = None
    last_name: Annotated[str | None, Field(alias="lastName", description="User's last name.")] = None
    email: Annotated[str, Field(description="User's email address.")] = ""
    email_verified: Annotated[bool, Field(alias="emailVerified", description="Whether the email is verified.")] = False
    enabled: Annotated[bool, Field(description="Whether the user account is enabled.")] = True
    attributes: Annotated[dict[str, list[str]], Field(description="Custom user attributes as key-value pairs.")] = {}
    created_timestamp: Annotated[
        int | None, Field(alias="createdTimestamp", description="Unix timestamp of account creation.")
    ] = None

    @computed_field
    @property
    def name(self) -> str:
        """Full display name, combining first and last name with username fallback."""
        full = f"{self.first_name or ''} {self.last_name or ''}".strip()
        return full or self.username
