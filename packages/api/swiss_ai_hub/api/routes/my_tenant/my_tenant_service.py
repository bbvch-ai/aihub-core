from fastapi import HTTPException
from swiss_ai_hub.core.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn
from swiss_ai_hub.core.persistence.access.entities.tenant_entity import TenantEntity
from swiss_ai_hub.core.persistence.access.entities.user_tenant_role_entity import UserTenantRoleEntity
from swiss_ai_hub.core.persistence.user.user_entity import UserEntity

from swiss_ai_hub.api.routes.my_tenant.dto.active_tenant_dto import ActiveTenantDTO
from swiss_ai_hub.api.routes.my_tenant.dto.tenant_membership_dto import TenantMembershipDTO


class MyTenantService:
    """Handles tenant-related operations for the logged-in user."""

    @staticmethod
    @trace_fn
    def get_my_tenants(user_id: str) -> list[TenantMembershipDTO]:
        """Returns all tenants the user belongs to."""
        tenant_ids = UserTenantRoleEntity.get_tenant_ids_for_user(user_id)
        tenants: list[TenantMembershipDTO] = []
        for tenant_id in tenant_ids:
            entity = TenantEntity.get_tenant_by_id(tenant_id)
            if entity:
                tenants.append(TenantMembershipDTO.from_entity(entity))
        return tenants

    @staticmethod
    @trace_fn
    def get_my_active_tenant(user_id: str) -> ActiveTenantDTO:
        """Returns the user's currently active tenant."""
        user = UserEntity.by_oid(user_id)
        if not user.active_tenant_id:
            raise HTTPException(status_code=404, detail="No active tenant set.")

        entity = TenantEntity.get_tenant_by_id(user.active_tenant_id)
        if not entity:
            raise HTTPException(status_code=404, detail="Active tenant no longer exists.")

        return ActiveTenantDTO.from_entity(entity)

    @staticmethod
    @trace_fn
    def set_my_active_tenant(user_id: str, tenant_id: str) -> ActiveTenantDTO:
        """Sets the user's active tenant after validating membership."""
        roles = UserTenantRoleEntity.get_roles_for_user_in_tenant(user_id, tenant_id)
        if not roles:
            raise HTTPException(status_code=403, detail="You are not a member of this tenant.")

        entity = TenantEntity.get_tenant_by_id(tenant_id)
        if not entity:
            raise HTTPException(status_code=404, detail="Tenant not found.")

        user = UserEntity.by_oid(user_id)
        user.set_active_tenant(tenant_id)

        return ActiveTenantDTO.from_entity(entity)
