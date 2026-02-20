from aihub_lib.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn
from aihub_lib.persistence.access.entities.RoleEntity import RoleEntity, UsageLimit
from fastapi import HTTPException

from aihub_api.routes.role.dto.CreateRoleRequest import CreateRoleRequest
from aihub_api.routes.role.dto.RoleResponse import RoleResponse
from aihub_api.routes.role.dto.UpdateRoleRequest import UpdateRoleRequest


class RoleService:
    @staticmethod
    @trace_fn
    def create_role(data: CreateRoleRequest, tenant_id: str) -> RoleResponse:
        """
        Creates a new tenant-scoped role.
        Raises NotUniqueError if a role with the same name already exists in this tenant.
        """
        role = RoleEntity.create_tenant_role(
            name=data.name,
            description=data.description,
            access_rules=data.access_rules,
            tenant_id=tenant_id,
            usage_limits=[UsageLimit(pattern=ul.pattern, limit=ul.limit, period=ul.period) for ul in data.usage_limits],
        )
        return RoleResponse.from_role_entity(role)

    @staticmethod
    @trace_fn
    def list_roles(tenant_id: str) -> list[RoleResponse]:
        """Lists all roles available to the tenant (system roles + tenant-specific roles)."""
        roles = RoleEntity.get_roles_for_tenant(tenant_id)
        return [RoleResponse.from_role_entity(role) for role in roles]

    @staticmethod
    @trace_fn
    def get_role_by_id(role_id: str, tenant_id: str) -> RoleResponse:
        """Retrieves a single role by its ID. Must belong to the given tenant or be a system role."""
        role = RoleEntity.objects.get(id=role_id)
        if role.tenant_id is not None and role.tenant_id != tenant_id:
            raise HTTPException(status_code=404, detail="Role not found.")
        return RoleResponse.from_role_entity(role)

    @staticmethod
    @trace_fn
    def update_role(role_id: str, data: UpdateRoleRequest, tenant_id: str) -> RoleResponse:
        """Updates an existing tenant-scoped role's fields."""
        role = RoleEntity.objects.get(id=role_id)
        if role.tenant_id is None:
            raise HTTPException(status_code=403, detail="Cannot modify system roles.")
        if role.tenant_id != tenant_id:
            raise HTTPException(status_code=404, detail="Role not found.")

        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return RoleResponse.from_role_entity(role)

        if "usage_limits" in update_data and data.usage_limits is not None:
            update_data["usage_limits"] = [
                UsageLimit(pattern=ul.pattern, limit=ul.limit, period=ul.period) for ul in data.usage_limits
            ]

        role.modify(**update_data)
        role.reload()
        return RoleResponse.from_role_entity(role)

    @staticmethod
    @trace_fn
    def delete_role(role_id: str, tenant_id: str) -> None:
        """Deletes a tenant-scoped role by its ID. System roles cannot be deleted."""
        role = RoleEntity.objects.get(id=role_id)
        if role.tenant_id is None:
            raise HTTPException(status_code=403, detail="Cannot delete system roles.")
        if role.tenant_id != tenant_id:
            raise HTTPException(status_code=404, detail="Role not found.")
        role.delete()
