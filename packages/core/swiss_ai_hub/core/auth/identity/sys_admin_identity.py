from typing import Annotated

from pydantic import BaseModel, Field


class SysAdminIdentity(BaseModel):
    """Lightweight identity for system administrators operating outside tenant context."""

    id: Annotated[str, Field(description="The unique identifier for the user (Keycloak sub).")]
    name: Annotated[str, Field(description="The display name of the user.")]
    email: Annotated[str, Field(description="The email address of the user.")]
