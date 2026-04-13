from datetime import datetime
from typing import Annotated, Self

from pydantic import BaseModel, Field
from swiss_ai_hub.core.persistence.access.entities.tenant_entity import TenantEntity


class TenantResponse(BaseModel):
    """Response model for a tenant."""

    id: Annotated[str, Field(description="Unique tenant identifier.")]
    name: Annotated[str, Field(description="Tenant display name.")]
    description: Annotated[str, Field(description="Tenant description.")]
    access_rules: Annotated[list[str], Field(description="Access rules granted to this tenant.")]
    is_default: Annotated[bool, Field(description="Whether this is the default tenant.")]
    created_at: Annotated[datetime, Field(description="Tenant creation timestamp.")]
    updated_at: Annotated[datetime, Field(description="Tenant last update timestamp.")]

    @classmethod
    def from_entity(cls, entity: TenantEntity) -> Self:
        return cls(
            id=str(entity.id),
            name=entity.name,
            description=entity.description or "",
            access_rules=entity.access_rules or [],
            is_default=entity.is_default,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
