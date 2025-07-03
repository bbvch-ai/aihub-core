from typing import List

from aihub_lib.persistence.access.entities.RoleEntity import RoleEntity

from aihub_api.routes.role.dto.CreateRoleRequest import CreateRoleRequest
from aihub_api.routes.role.dto.RoleResponse import RoleResponse
from aihub_api.routes.role.dto.UpdateRoleRequest import UpdateRoleRequest


class RoleService:
    @staticmethod
    def create_role(data: CreateRoleRequest) -> RoleResponse:
        """
        Creates a new role.
        Raises NotUniqueError if a role with the same name already exists.
        """
        role = RoleEntity(name=data.name, description=data.description, access_rules=data.access_rules)
        role.save()
        return RoleResponse.model_validate(role)

    @staticmethod
    def list_roles() -> List[RoleResponse]:
        """Lists all roles in the database."""
        roles = RoleEntity.objects()
        return [RoleResponse.model_validate(role) for role in roles]

    @staticmethod
    def get_role_by_id(role_id: str) -> RoleResponse:
        """
        Retrieves a single role by its ID.
        Raises DoesNotExist if the role is not found.
        """
        role = RoleEntity.objects.get(id=role_id)
        return RoleResponse.model_validate(role)

    @staticmethod
    def update_role(role_id: str, data: UpdateRoleRequest) -> RoleResponse:
        """
        Updates an existing role's fields.
        Raises DoesNotExist if the role is not found.
        Raises NotUniqueError if the new name conflicts with an existing role.
        """
        role = RoleEntity.objects.get(id=role_id)
        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            # Nothing to update
            return RoleResponse.model_validate(role)

        role.modify(**update_data)
        role.reload()
        return RoleResponse.model_validate(role)

    @staticmethod
    def delete_role(role_id: str) -> None:
        """
        Deletes a role by its ID.
        Raises DoesNotExist if the role is not found.
        """
        role = RoleEntity.objects.get(id=role_id)
        role.delete()
