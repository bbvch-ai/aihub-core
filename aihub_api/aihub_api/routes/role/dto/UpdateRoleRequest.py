from typing import Annotated

from pydantic import BaseModel, Field


class UpdateRoleRequest(BaseModel):
    """Request model for updating an existing role. All fields are optional."""

    name: Annotated[str | None, Field(description="The new unique name of the role.")] = None
    description: Annotated[str | None, Field(description="The new description for the role.")] = None
    access_rules: Annotated[list[str] | None, Field(description="The new list of access rules.")] = None
    agent_calls_limit: Annotated[
        int | None, Field(description="Maximum agent calls per period. None means unlimited.")
    ] = None
    agent_calls_period: Annotated[
        str | None, Field(description="Period for agent call limit reset (e.g., '1mo', '1d', '1h').")
    ] = None
