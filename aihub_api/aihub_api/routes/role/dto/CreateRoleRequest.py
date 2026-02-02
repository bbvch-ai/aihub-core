from typing import Annotated

from pydantic import BaseModel, Field


class UsageLimitDTO(BaseModel):
    """Pattern-based usage limit rule."""

    pattern: Annotated[
        str,
        Field(
            description="Full dotted resource pattern with wildcards "
            "(e.g. 'aihub.user.agent.>', 'aihub.user.process.MyProcess.*'). "
        ),
    ]
    limit: Annotated[int, Field(description="Max calls per period for this pattern.")]
    period: Annotated[str, Field(description="Period for limit: 1h, 1d, 7d, 1mo.")]


class CreateRoleRequest(BaseModel):
    """Request model for creating a new role."""

    name: Annotated[str, Field(description="The unique name of the role.")]
    description: Annotated[str, Field(description="A short description of the role's purpose.")]
    access_rules: Annotated[list[str], Field(description="A list of access rules granted by this role.")] = []
    usage_limits: Annotated[list[UsageLimitDTO], Field(description="Pattern-based usage limit rules.")] = []
