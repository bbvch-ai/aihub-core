from datetime import datetime
from typing import Annotated

from aihub_lib.persistence.expert.ExpertGroupEntity import ExpertGroupEntity
from pydantic import BaseModel, Field


class ExpertGroupResponse(BaseModel):
    """Response model representing an expert group."""

    model_config = {"from_attributes": True}

    id: Annotated[str, Field(description="The unique identifier of the expert group.")]
    name: Annotated[str, Field(description="The name of the expert group.")]
    description: Annotated[str | None, Field(description="The description of the expert group.")]
    member_user_ids: Annotated[list[str], Field(description="The list of member user IDs.")]
    created_at: Annotated[datetime, Field(description="When the group was created.")]
    updated_at: Annotated[datetime, Field(description="When the group was last updated.")]

    @classmethod
    def from_entity(cls, entity: ExpertGroupEntity) -> "ExpertGroupResponse":
        return cls(
            id=str(entity.id),
            name=entity.name,
            description=entity.description,
            member_user_ids=list(entity.member_user_ids),
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
