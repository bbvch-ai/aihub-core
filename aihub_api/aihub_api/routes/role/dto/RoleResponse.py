from typing import Annotated, Self

from aihub_lib.persistence.access.entities.RoleEntity import RoleEntity
from pydantic import BaseModel, Field

from aihub_api.routes.role.dto.UsageLimitDTO import UsageLimitDTO


class RoleResponse(BaseModel):
    """Response model representing a role."""

    model_config = {"from_attributes": True}

    id: Annotated[str, Field(description="The unique identifier of the role.")]
    name: Annotated[str, Field(description="The name of the role.")]
    description: Annotated[str, Field(description="The description of the role.")]
    access_rules: Annotated[list[str], Field(description="The list of access rules for the role.")]
    usage_limits: Annotated[list[UsageLimitDTO], Field(description="Pattern-based usage limit rules.")] = []

    @classmethod
    def from_role_entity(cls, role_entity: RoleEntity) -> Self:
        return cls(
            id=str(role_entity.id),
            name=role_entity.name,
            description=role_entity.description,
            access_rules=role_entity.access_rules,
            usage_limits=[
                UsageLimitDTO(
                    pattern=usage_limit.pattern,
                    limit=usage_limit.limit,
                    period=usage_limit.period,
                )
                for usage_limit in (role_entity.usage_limits or [])
            ],
        )
