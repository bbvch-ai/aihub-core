from typing import Annotated

from pydantic import BaseModel, Field


class UserIdentity(BaseModel):
    id: Annotated[str, Field(description="The unique identifier for the user.")]
    name: Annotated[str, Field(description="The name of the user.")]
    email: Annotated[str, Field(description="The email address of the user.")]
    roles: Annotated[list[str], Field(description="The roles assigned to the user.")]
    profile_image: Annotated[str | None, Field(description="Data URL (base64) representation of profile image")] = None
