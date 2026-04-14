from fastapi import HTTPException
from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.auth.keycloak.keycloak_admin_service import KeycloakAdminService
from swiss_ai_hub.core.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn
from swiss_ai_hub.core.persistence.access.entities.tenant_metadata_entity import TenantMetadataEntity
from swiss_ai_hub.core.persistence.access.entities.user_tenant_role_entity import UserTenantRoleEntity

from swiss_ai_hub.api.routes.my_tenant.dto.active_tenant_dto import ActiveTenantDTO
from swiss_ai_hub.api.routes.my_tenant.dto.my_tenants_response import MyTenantsResponse
from swiss_ai_hub.api.routes.my_tenant.dto.tenant_membership_dto import TenantMembershipDTO


class MyTenantService:
    """Handles tenant-related operations for the logged-in user.

    Keycloak is the source of truth for tenant existence; this service treats any
    tenant_id that is not currently a Keycloak group under ``/tenants/`` as
    non-existent, regardless of what the metadata collection contains. The
    metadata collection is consulted only for display fields (name, description).
    """

    @staticmethod
    @trace_fn
    async def get_my_tenants(user: UserIdentity) -> MyTenantsResponse:
        """Returns all tenants the user belongs to, along with sysadmin status.

        ``is_sys_admin`` is sourced from the JWT realm role claim (populated in
        ``UserIdentity`` by the Keycloak auth handler). The set of tenants is
        filtered through Keycloak so orphaned metadata records (Keycloak group
        deleted but MongoDB record remains) are not surfaced to end users.
        """
        tenant_ids = UserTenantRoleEntity.get_tenant_ids_for_user(user.id)
        if not tenant_ids:
            return MyTenantsResponse(tenants=[], is_sys_admin=user.is_sys_admin)

        existing_tenant_ids = await KeycloakAdminService.filter_existing_tenant_ids(tenant_ids)
        if not existing_tenant_ids:
            return MyTenantsResponse(tenants=[], is_sys_admin=user.is_sys_admin)

        tenant_entities = TenantMetadataEntity.objects(id__in=list(existing_tenant_ids))
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
        """Sets the user's active tenant after validating existence and membership.

        Existence is validated against Keycloak (source of truth). Membership is
        validated against the tenant role table, which is itself synced from the
        JWT ``tenants`` claim at login.
        """
        if not await KeycloakAdminService.tenant_exists(tenant_id):
            raise HTTPException(status_code=404, detail="Tenant not found.")

        roles = UserTenantRoleEntity.get_roles_for_user_in_tenant(user_id, tenant_id)
        if not roles:
            raise HTTPException(status_code=403, detail="You are not a member of this tenant.")

        entity = TenantMetadataEntity.get_metadata_by_tenant_id(tenant_id)
        if not entity:
            raise HTTPException(status_code=404, detail="Tenant metadata not configured.")

        await KeycloakAdminService.set_active_tenant(user_id, tenant_id)

        return ActiveTenantDTO.from_entity(entity)
