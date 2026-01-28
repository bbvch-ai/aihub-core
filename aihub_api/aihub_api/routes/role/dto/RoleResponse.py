from typing import Annotated

from aihub_lib.persistence.access.entities.RoleEntity import RoleEntity
from pydantic import BaseModel, Field


class RoleResponse(BaseModel):
    """Response model representing a role."""

    model_config = {"from_attributes": True}

    id: Annotated[str, Field(description="The unique identifier of the role.")]
    name: Annotated[str, Field(description="The name of the role.")]
    description: Annotated[str, Field(description="The description of the role.")]
    access_rules: Annotated[list[str], Field(description="The list of access rules for the role.")]
    agent_calls_limit: Annotated[
        int | None, Field(description="Maximum agent calls per period. None means unlimited.")
    ] = None
    agent_calls_period: Annotated[
        str, Field(description="Period for agent call limit reset (e.g., '1mo', '1d', '1h').")
    ] = "1mo"

    @classmethod
    def from_role_entity(cls, role_entity: RoleEntity):
        return cls(
            id=str(role_entity.id),
            name=role_entity.name,
            description=role_entity.description,
            access_rules=role_entity.access_rules,
            agent_calls_limit=role_entity.agent_calls_limit,
            agent_calls_period=role_entity.agent_calls_period or "1mo",
        )
