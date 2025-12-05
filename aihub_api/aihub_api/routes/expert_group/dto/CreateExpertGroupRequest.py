from typing import Annotated

from pydantic import BaseModel, Field


class CreateExpertGroupRequest(BaseModel):
    """Request model for creating a new expert group."""

    name: Annotated[str, Field(description="The unique name of the expert group.")]
    description: Annotated[str | None, Field(description="A short description of the group's purpose.")] = None
    member_user_ids: Annotated[list[str], Field(description="List of user IDs who are members of this group.")] = []
