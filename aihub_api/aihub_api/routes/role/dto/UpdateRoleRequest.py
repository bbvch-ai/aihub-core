from typing import Annotated

from pydantic import BaseModel, Field

from aihub_api.routes.role.dto.UsageLimitDTO import UsageLimitDTO


class UpdateRoleRequest(BaseModel):
    """Request model for updating an existing role. All fields are optional."""

    name: Annotated[str | None, Field(description="The new unique name of the role.")] = None
    description: Annotated[str | None, Field(description="The new description for the role.")] = None
    access_rules: Annotated[list[str] | None, Field(description="The new list of access rules.")] = None
    usage_limits: Annotated[list[UsageLimitDTO] | None, Field(description="Pattern-based usage limit rules.")] = None
