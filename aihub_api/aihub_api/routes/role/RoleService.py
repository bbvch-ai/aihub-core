from aihub_lib.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn
from aihub_lib.persistence.access.entities.RoleEntity import RoleEntity, UsageLimit

from aihub_api.routes.role.dto.CreateRoleRequest import CreateRoleRequest
from aihub_api.routes.role.dto.RoleResponse import RoleResponse
from aihub_api.routes.role.dto.UpdateRoleRequest import UpdateRoleRequest


class RoleService:
    @staticmethod
    @trace_fn
    def create_role(data: CreateRoleRequest) -> RoleResponse:
        """
        Creates a new role.
        Raises NotUniqueError if a role with the same name already exists.
        """
        role = RoleEntity(
            name=data.name,
            description=data.description,
            access_rules=data.access_rules,
            usage_limits=[UsageLimit(pattern=ul.pattern, limit=ul.limit, period=ul.period) for ul in data.usage_limits],
        )
        role.save()
        return RoleResponse.from_role_entity(role)

    @staticmethod
    @trace_fn
    def list_roles() -> list[RoleResponse]:
        """Lists all roles in the database."""
        roles = RoleEntity.objects()
        return [RoleResponse.from_role_entity(role) for role in roles]

    @staticmethod
    @trace_fn
    def get_role_by_id(role_id: str) -> RoleResponse:
        """
        Retrieves a single role by its ID.
        Raises DoesNotExist if the role is not found.
        """
        role = RoleEntity.objects.get(id=role_id)
        return RoleResponse.from_role_entity(role)

    @staticmethod
    @trace_fn
    def update_role(role_id: str, data: UpdateRoleRequest) -> RoleResponse:
        """
        Updates an existing role's fields.
        Raises DoesNotExist if the role is not found.
        Raises NotUniqueError if the new name conflicts with an existing role.
        """
        role = RoleEntity.objects.get(id=role_id)
        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return RoleResponse.from_role_entity(role)

        if "usage_limits" in update_data:
            update_data["usage_limits"] = [
                UsageLimit(pattern=ul["pattern"], limit=ul["limit"], period=ul["period"])
                for ul in update_data["usage_limits"]
            ]

        role.modify(**update_data)
        role.reload()
        return RoleResponse.from_role_entity(role)

    @staticmethod
    @trace_fn
    def delete_role(role_id: str) -> None:
        """
        Deletes a role by its ID.
        Raises DoesNotExist if the role is not found.
        """
        role = RoleEntity.objects.get(id=role_id)
        role.delete()
