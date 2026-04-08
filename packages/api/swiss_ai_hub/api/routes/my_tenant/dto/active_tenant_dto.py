from typing import Annotated, Self

from pydantic import BaseModel, Field
from swiss_ai_hub.core.persistence.access.entities.tenant_entity import TenantEntity


class ActiveTenantDTO(BaseModel):
    """The user's currently active tenant."""

    id: Annotated[str, Field(description="Tenant identifier")]
    name: Annotated[str, Field(description="Tenant display name")]

    @classmethod
    def from_entity(cls, entity: TenantEntity) -> Self:
        return cls(
            id=str(entity.id),
            name=entity.name,
        )
