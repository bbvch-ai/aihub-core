from fastapi import HTTPException
from swiss_ai_hub.core.auth import AccessChecker
from swiss_ai_hub.core.infrastructure import trace_fn
from swiss_ai_hub.core.persistence.access.entities.role_entity import RoleEntity, UsageLimit

from swiss_ai_hub.api.routes.role.dto.create_role_request import CreateRoleRequest
from swiss_ai_hub.api.routes.role.dto.role_response import RoleResponse
from swiss_ai_hub.api.routes.role.dto.update_role_request import UpdateRoleRequest

_ROLE_NOT_FOUND = "Role not found."


class RoleService:
    @staticmethod
    @trace_fn
    async def create_role(data: CreateRoleRequest, tenant_id: str) -> RoleResponse:
        """
        Creates a new tenant-scoped role.
        Raises pymongo's DuplicateKeyError if a role with the same name already exists in this tenant.
        """
        role = await RoleEntity.create_tenant_role(
            name=data.name,
            description=data.description,
            access_rules=[AccessChecker.normalize_model_access_rule(rule) for rule in data.access_rules],
            tenant_id=tenant_id,
            usage_limits=[UsageLimit(pattern=ul.pattern, limit=ul.limit, period=ul.period) for ul in data.usage_limits],
        )
        return RoleResponse.from_role_entity(role)

    @staticmethod
    @trace_fn
    async def list_roles(tenant_id: str) -> list[RoleResponse]:
        """Lists all roles available to the tenant (system roles + tenant-specific roles)."""
        roles = await RoleEntity.get_roles_for_tenant(tenant_id)
        return [RoleResponse.from_role_entity(role) for role in roles]

    @staticmethod
    @trace_fn
    async def get_role_by_id(role_id: str, tenant_id: str) -> RoleResponse:
        """Retrieves a single role by its ID. Must belong to the given tenant or be a system role."""
        role = await RoleEntity.get(role_id)
        if role is None:
            raise HTTPException(status_code=404, detail=_ROLE_NOT_FOUND)
        if role.tenant_id is not None and role.tenant_id != tenant_id:
            raise HTTPException(status_code=404, detail=_ROLE_NOT_FOUND)
        return RoleResponse.from_role_entity(role)

    @staticmethod
    @trace_fn
    async def update_role(role_id: str, data: UpdateRoleRequest, tenant_id: str) -> RoleResponse:
        """Updates an existing tenant-scoped role's fields."""
        role = await RoleEntity.get(role_id)
        if role is None:
            raise HTTPException(status_code=404, detail=_ROLE_NOT_FOUND)
        if role.tenant_id is None:
            raise HTTPException(status_code=403, detail="Cannot modify system roles.")
        if role.tenant_id != tenant_id:
            raise HTTPException(status_code=404, detail=_ROLE_NOT_FOUND)
        # Users are assigned roles by name, so a rename would orphan every existing assignment.
        if "name" in data.model_fields_set and data.name != role.name:
            raise HTTPException(status_code=400, detail="Roles cannot be renamed.")

        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return RoleResponse.from_role_entity(role)

        if "access_rules" in update_data and data.access_rules is not None:
            update_data["access_rules"] = [
                AccessChecker.normalize_model_access_rule(rule) for rule in data.access_rules
            ]

        if "usage_limits" in update_data and data.usage_limits is not None:
            update_data["usage_limits"] = [
                UsageLimit(pattern=ul.pattern, limit=ul.limit, period=ul.period) for ul in data.usage_limits
            ]

        # Saved through the document (not a query update) so its event fires and AccessChangeHook
        # re-syncs OpenWebUI access grants when a role's rules change.
        for field, value in update_data.items():
            setattr(role, field, value)
        await role.save_changes()
        return RoleResponse.from_role_entity(role)

    @staticmethod
    @trace_fn
    async def delete_role(role_id: str, tenant_id: str) -> None:
        """Deletes a tenant-scoped role by its ID. System roles cannot be deleted."""
        role = await RoleEntity.get(role_id)
        if role is None:
            raise HTTPException(status_code=404, detail=_ROLE_NOT_FOUND)
        if role.tenant_id is None:
            raise HTTPException(status_code=403, detail="Cannot delete system roles.")
        if role.tenant_id != tenant_id:
            raise HTTPException(status_code=404, detail=_ROLE_NOT_FOUND)
        await role.delete()
