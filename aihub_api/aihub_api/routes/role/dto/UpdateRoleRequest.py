from typing import Annotated, List, Optional

from pydantic import BaseModel, Field


class UpdateRoleRequest(BaseModel):
    """Request model for updating an existing role. All fields are optional."""

    name: Annotated[Optional[str], Field(description="The new unique name of the role.")] = None
    description: Annotated[Optional[str], Field(description="The new description for the role.")] = None
    access_rules: Annotated[Optional[List[str]], Field(description="The new list of access rules.")] = None
