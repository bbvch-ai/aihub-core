from typing import Annotated, List

from pydantic import BaseModel, Field

from aihub_lib.persistence.access.entities.RoleEntity import RoleEntity


class RoleResponse(BaseModel):
    """Response model representing a role."""

    model_config = {"from_attributes": True}

    id: Annotated[str, Field(description="The unique identifier of the role.")]
    name: Annotated[str, Field(description="The name of the role.")]
    description: Annotated[str, Field(description="The description of the role.")]
    access_rules: Annotated[List[str], Field(description="The list of access rules for the role.")]

    @classmethod
    def from_role_entity(cls, role_entity: RoleEntity):
        return cls(
            id=str(role_entity.id),
            name=role_entity.name,
            description=role_entity.description,
            access_rules=role_entity.access_rules,
        )