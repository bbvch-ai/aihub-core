from typing import Annotated

from pydantic import BaseModel, Field

from aihub_api.routes.role.dto.UsageLimitDTO import UsageLimitDTO


class CreateRoleRequest(BaseModel):
    """Request model for creating a new role."""

    name: Annotated[str, Field(description="The unique name of the role.")]
    description: Annotated[str, Field(description="A short description of the role's purpose.")]
    access_rules: Annotated[list[str], Field(description="A list of access rules granted by this role.")] = []
    usage_limits: Annotated[list[UsageLimitDTO], Field(description="Pattern-based usage limit rules.")] = []
