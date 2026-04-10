from typing import Annotated

from pydantic import BaseModel, Field

from swiss_ai_hub.core.auth.identity.tenant_identity import TenantIdentity


class UserIdentity(BaseModel):
    """Lightweight identity object for authenticated users."""

    id: Annotated[str, Field(description="The unique identifier for the user.")]
    name: Annotated[str, Field(description="The name of the user.")]
    email: Annotated[str, Field(description="The email address of the user.")]
    roles: Annotated[list[str], Field(description="The roles assigned to the user within the acting tenant.")]
    acting_within_tenant: Annotated[
        TenantIdentity | None, Field(description="The tenant context the user is operating within.")
    ] = None

    @classmethod
    def from_user_entity(cls, user: UserEntity, tenant: TenantIdentity) -> Self:
        """Create a UserIdentity from a UserEntity and tenant context."""
        return cls(
            id=user.id,
            name=user.name,
            email=user.email,
            roles=user.get_roles(tenant.id),
            acting_within_tenant=tenant,
        )

    @classmethod
    def from_user_entity_without_tenant(cls, user: UserEntity) -> Self:
        """Create a UserIdentity without tenant context, for global (non-tenant-scoped) endpoints."""
        return cls(
            id=user.id,
            name=user.name,
            email=user.email,
            roles=[],
        )
