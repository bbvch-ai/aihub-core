from typing import Annotated, Self

from pydantic import BaseModel, Field

from swiss_ai_hub.core.persistence.access.entities.tenant_metadata_entity import TenantMetadataEntity


class TenantIdentity(BaseModel):
    """Represents a tenant's identity in the multi-tenant system."""

    id: Annotated[str, Field(description="Unique tenant identifier")]
    name: Annotated[str, Field(description="Tenant display name")]
    access_rules: Annotated[list[str], Field(description="Access rules granted to this tenant")]

    @classmethod
    def from_tenant_metadata_entity(cls, tenant: TenantMetadataEntity) -> Self:
        """Build a TenantIdentity from stored metadata.

        Assumes the caller has already verified the tenant exists in Keycloak —
        metadata alone is not proof of existence.
        """
        return cls(
            id=str(tenant.id),
            name=tenant.name,
            access_rules=tenant.access_rules,
        )
