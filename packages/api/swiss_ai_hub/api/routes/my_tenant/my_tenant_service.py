from fastapi import HTTPException
from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.auth.keycloak.keycloak_admin_service import KeycloakAdminService
from swiss_ai_hub.core.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn
from swiss_ai_hub.core.persistence.access.entities.tenant_entity import TenantEntity
from swiss_ai_hub.core.persistence.access.entities.user_tenant_role_entity import UserTenantRoleEntity

from swiss_ai_hub.api.routes.my_tenant.dto.active_tenant_dto import ActiveTenantDTO
from swiss_ai_hub.api.routes.my_tenant.dto.my_tenants_response import MyTenantsResponse
from swiss_ai_hub.api.routes.my_tenant.dto.tenant_membership_dto import TenantMembershipDTO


class MyTenantService:
    """Handles tenant-related operations for the logged-in user."""

    @staticmethod
    @trace_fn
    def get_my_tenants(user: UserIdentity) -> MyTenantsResponse:
        """Returns all tenants the user belongs to, along with sysadmin status.

        `is_sys_admin` is sourced from the JWT realm role claim (populated in `UserIdentity`
        by the Keycloak auth handler), so no Keycloak Admin API call is required here.
        """
        tenant_ids = UserTenantRoleEntity.get_tenant_ids_for_user(user.id)
        if not tenant_ids:
            return MyTenantsResponse(tenants=[], is_sys_admin=user.is_sys_admin)

        tenant_entities = TenantEntity.objects(id__in=tenant_ids)
        tenants = [TenantMembershipDTO.from_entity(entity) for entity in tenant_entities]
        return MyTenantsResponse(tenants=tenants, is_sys_admin=user.is_sys_admin)

    @staticmethod
    @trace_fn
    async def get_my_active_tenant(user_id: str) -> ActiveTenantDTO:
        """Returns the user's currently active tenant."""
        active_tenant_id = await KeycloakAdminService.get_active_tenant_id(user_id)
        if not active_tenant_id:
            raise HTTPException(status_code=404, detail="No active tenant set.")

        entity = TenantEntity.get_tenant_by_id(active_tenant_id)
        if not entity:
            raise HTTPException(status_code=404, detail="Active tenant no longer exists.")

        return ActiveTenantDTO.from_entity(entity)

    @staticmethod
    @trace_fn
    async def set_my_active_tenant(user_id: str, tenant_id: str) -> ActiveTenantDTO:
        """Sets the user's active tenant after validating membership."""
        roles = UserTenantRoleEntity.get_roles_for_user_in_tenant(user_id, tenant_id)
        if not roles:
            raise HTTPException(status_code=403, detail="You are not a member of this tenant.")

        entity = TenantEntity.get_tenant_by_id(tenant_id)
        if not entity:
            raise HTTPException(status_code=404, detail="Tenant not found.")

        await KeycloakAdminService.set_active_tenant(user_id, tenant_id)

        return ActiveTenantDTO.from_entity(entity)
