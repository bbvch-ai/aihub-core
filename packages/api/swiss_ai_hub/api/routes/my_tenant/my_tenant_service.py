from fastapi import HTTPException
from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.auth.keycloak.keycloak_admin_service import KeycloakAdminService
from swiss_ai_hub.core.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn
from swiss_ai_hub.core.persistence.access.entities.tenant_metadata_entity import TenantMetadataEntity

from swiss_ai_hub.api.routes.my_tenant.dto.active_tenant_dto import ActiveTenantDTO
from swiss_ai_hub.api.routes.my_tenant.dto.my_tenants_response import MyTenantsResponse
from swiss_ai_hub.api.routes.my_tenant.dto.tenant_membership_dto import TenantMembershipDTO


class MyTenantService:
    """Handles tenant-related operations for the logged-in user.

    Keycloak is the sole source of truth for tenant existence AND tenant membership.
    The metadata collection is consulted only for display fields (name, description).
    Membership and permissions are orthogonal: ``AIHubSysAdmin`` grants admin-level
    permissions within a tenant but does NOT grant membership. The superuser sees
    every tenant because they are explicitly added to every tenant group on creation
    (ADR ``2026_04_15_superuser_added_to_every_new_tenant``), not because of any role.
    """

    @staticmethod
    @trace_fn
    async def get_my_tenants(user: UserIdentity) -> MyTenantsResponse:
        """Returns all tenants the user is a member of in Keycloak, along with sysadmin status."""
        tenant_ids = await KeycloakAdminService.get_user_tenant_ids(user.id)
        if not tenant_ids:
            return MyTenantsResponse(tenants=[], is_sys_admin=user.is_sys_admin)

        tenant_entities = TenantMetadataEntity.objects(id__in=list(tenant_ids))
        tenants = [TenantMembershipDTO.from_entity(entity) for entity in tenant_entities]
        return MyTenantsResponse(tenants=tenants, is_sys_admin=user.is_sys_admin)

    @staticmethod
    @trace_fn
    async def get_my_active_tenant(user_id: str) -> ActiveTenantDTO:
        """Returns the user's currently active tenant.

        Existence is verified against Keycloak; the metadata collection is only
        used for the display name.
        """
        active_tenant_id = await KeycloakAdminService.get_active_tenant_id(user_id)
        if not active_tenant_id:
            raise HTTPException(status_code=404, detail="No active tenant set.")

        if not await KeycloakAdminService.tenant_exists(active_tenant_id):
            await KeycloakAdminService.clear_active_tenant(user_id)
            raise HTTPException(status_code=404, detail="Active tenant no longer exists.")

        entity = TenantMetadataEntity.get_metadata_by_tenant_id(active_tenant_id)
        if not entity:
            raise HTTPException(status_code=404, detail="Active tenant metadata not configured.")

        return ActiveTenantDTO.from_entity(entity)

    @staticmethod
    @trace_fn
    async def set_my_active_tenant(user_id: str, tenant_id: str) -> ActiveTenantDTO:
        """Sets the user's active tenant after validating existence and Keycloak membership."""
        if not await KeycloakAdminService.tenant_exists(tenant_id):
            raise HTTPException(status_code=404, detail="Tenant not found.")

        if not await KeycloakAdminService.is_user_member_of_tenant(user_id, tenant_id):
            raise HTTPException(status_code=403, detail="You are not a member of this tenant.")

        entity = TenantMetadataEntity.get_metadata_by_tenant_id(tenant_id)
        if not entity:
            raise HTTPException(status_code=404, detail="Tenant metadata not configured.")

        await KeycloakAdminService.set_active_tenant(user_id, tenant_id)

        return ActiveTenantDTO.from_entity(entity)
