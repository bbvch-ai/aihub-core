from typing import Annotated

from pydantic import BaseModel, Field


class UpdateExpertGroupRequest(BaseModel):
    """Request model for updating an expert group."""

    name: Annotated[str | None, Field(description="The unique name of the expert group.")] = None
    description: Annotated[str | None, Field(description="A short description of the group's purpose.")] = None
    member_user_ids: Annotated[
        list[str] | None, Field(description="List of user IDs who are members of this group.")
    ] = None
