from typing import Annotated

from pydantic import BaseModel, Field


class CreateRoleRequest(BaseModel):
    """Request model for creating a new role."""

    name: Annotated[str, Field(description="The unique name of the role.")]
    description: Annotated[str, Field(description="A short description of the role's purpose.")]
    access_rules: Annotated[list[str], Field(description="A list of access rules granted by this role.")] = []
    agent_calls_limit: Annotated[
        int | None, Field(description="Maximum agent calls per period. None means unlimited.")
    ] = None
    agent_calls_period: Annotated[
        str, Field(description="Period for agent call limit reset (e.g., '1mo', '1d', '1h').")
    ] = "1mo"
