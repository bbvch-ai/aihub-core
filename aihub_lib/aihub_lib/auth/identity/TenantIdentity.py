from typing import Annotated, Self

from pydantic import BaseModel, Field

from aihub_lib.persistence.access.entities.TenantEntity import TenantEntity


class TenantIdentity(BaseModel):
    """Represents a tenant's identity in the multi-tenant system."""

    id: Annotated[str, Field(description="Unique tenant identifier")]
    name: Annotated[str, Field(description="Tenant display name")]
    access_rules: Annotated[list[str], Field(description="Access rules granted to this tenant")]

    @classmethod
    def from_tenant_entity(cls, tenant: TenantEntity) -> Self:
        """Create a TenantIdentity from a TenantEntity database object."""
        return cls(
            id=tenant.id,
            name=tenant.name,
            access_rules=tenant.access_rules,
        )
