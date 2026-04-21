from datetime import datetime
from typing import Annotated, Self

from pydantic import BaseModel, Field
from swiss_ai_hub.core.persistence.access.entities.tenant_metadata_entity import TenantMetadataEntity

from swiss_ai_hub.api.routes.tenant_admin.dto.tenant_state import TenantState


class TenantResponse(BaseModel):
    """Response model for a tenant, as seen by sysadmins."""

    id: Annotated[str, Field(description="Unique tenant identifier (matches the Keycloak group name).")]
    name: Annotated[str, Field(description="Tenant display name.")]
    description: Annotated[str, Field(description="Tenant description.")]
    access_rules: Annotated[list[str], Field(description="Access rules granted to this tenant.")]
    state: Annotated[
        TenantState, Field(description="Whether the tenant also exists in Keycloak (active) or not (orphaned).")
    ]
    created_at: Annotated[datetime, Field(description="Tenant creation timestamp.")]
    updated_at: Annotated[datetime, Field(description="Tenant last update timestamp.")]

    @classmethod
    def from_entity(cls, entity: TenantMetadataEntity, *, state: TenantState = TenantState.ACTIVE) -> Self:
        return cls(
            id=str(entity.id),
            name=entity.name,
            description=entity.description or "",
            access_rules=entity.access_rules or [],
            state=state,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
