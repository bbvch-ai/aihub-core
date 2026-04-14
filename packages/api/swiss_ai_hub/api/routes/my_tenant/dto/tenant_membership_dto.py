from typing import Annotated, Self

from pydantic import BaseModel, Field
from swiss_ai_hub.core.persistence.access.entities.tenant_metadata_entity import TenantMetadataEntity


class TenantMembershipDTO(BaseModel):
    """A tenant the current user belongs to."""

    id: Annotated[str, Field(description="Tenant identifier")]
    name: Annotated[str, Field(description="Tenant display name")]
    description: Annotated[str, Field(description="Tenant description")]

    @classmethod
    def from_entity(cls, entity: TenantMetadataEntity) -> Self:
        return cls(
            id=str(entity.id),
            name=entity.name,
            description=entity.description or "",
        )
