from typing import Annotated, List
from fastapi import HTTPException, Security, status
from mongoengine.errors import DoesNotExist, NotUniqueError

from aihub_lib.auth.dependencies.AuthHandler import AuthHandler
from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.routes.Controller import Controller

from .RoleService import RoleService
from .dto.CreateRoleRequest import CreateRoleRequest
from .dto.DeleteRoleResponse import DeleteRoleResponse
from .dto.RoleResponse import RoleResponse
from .dto.UpdateRoleRequest import UpdateRoleRequest


class RoleController(Controller):
    name = LocaleString(en="Role")
    description = LocaleString(en="Manage user roles and permissions")
    icon = "solar:users-group-rounded-bold"

    def __init__(self, *, auth: AuthHandler, route: str = "/roles"):
        super().__init__(auth=auth, route=route)

    def create_role(self, route: str = "/") -> "RoleController":
        @self.router.post(
            route,
            summary="Create Role",
            description="Creates a new role with a name, description, and access rules.",
            status_code=status.HTTP_201_CREATED,
            tags=self.tags,
        )
        async def create_role_endpoint(
            role_data: CreateRoleRequest,
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.admin.role.create"))],
        ) -> RoleResponse:
            try:
                return RoleService.create_role(role_data)
            except NotUniqueError:
                raise HTTPException(status_code=409, detail=f"Role with name '{role_data.name}' already exists.")
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
        return self

    def list_roles(self, route: str = "/") -> "RoleController":
        @self.router.get(
            route,
            summary="List Roles",
            description="Retrieves a list of all available roles.",
            tags=self.tags,
        )
        async def list_roles_endpoint(
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.admin.role.read"))],
        ) -> List[RoleResponse]:
            return RoleService.list_roles()
        return self

    def get_role(self, route: str = "/{role_id}") -> "RoleController":
        @self.router.get(
            route,
            summary="Get Role",
            description="Retrieves a single role by its unique ID.",
            tags=self.tags,
        )
        async def get_role_endpoint(
            role_id: str,
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.admin.role.read"))],
        ) -> RoleResponse:
            try:
                return RoleService.get_role_by_id(role_id)
            except DoesNotExist:
                raise HTTPException(status_code=404, detail="Role not found.")
        return self

    def update_role(self, route: str = "/{role_id}") -> "RoleController":
        @self.router.patch(
            route,
            summary="Update Role",
            description="Updates a role's name, description, or access rules.",
            tags=self.tags,
        )
        async def update_role_endpoint(
            role_id: str,
            role_data: UpdateRoleRequest,
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.admin.role.update"))],
        ) -> RoleResponse:
            try:
                return RoleService.update_role(role_id, role_data)
            except DoesNotExist:
                raise HTTPException(status_code=404, detail="Role not found.")
            except NotUniqueError:
                raise HTTPException(status_code=409, detail=f"Role with name '{role_data.name}' already exists.")
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
        return self

    def delete_role(self, route: str = "/{role_id}") -> "RoleController":
        @self.router.delete(
            route,
            summary="Delete Role",
            description="Permanently deletes a role.",
            tags=self.tags,
        )
        async def delete_role_endpoint(
            role_id: str,
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.admin.role.delete"))],
        ) -> DeleteRoleResponse:
            try:
                RoleService.delete_role(role_id)
                return DeleteRoleResponse()
            except DoesNotExist:
                raise HTTPException(status_code=404, detail="Role not found.")
        return self