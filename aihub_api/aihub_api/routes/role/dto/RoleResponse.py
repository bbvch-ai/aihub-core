from typing import Annotated, List

from pydantic import BaseModel, Field


class RoleResponse(BaseModel):
    """Response model representing a role."""

    model_config = {"from_attributes": True}

    id: Annotated[str, Field(description="The unique identifier of the role.")]
    name: Annotated[str, Field(description="The name of the role.")]
    description: Annotated[str, Field(description="The description of the role.")]
    access_rules: Annotated[List[str], Field(description="The list of access rules for the role.")]
