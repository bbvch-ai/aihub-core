from typing import Annotated, Self

from aihub_lib.auth.dependencies.AuthHandler import AuthHandler
from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.routes.Controller import Controller
from fastapi import HTTPException, Security, status
from mongoengine.errors import DoesNotExist, NotUniqueError

from aihub_api.i18n.ApiLocaleString import ApiLocaleString

from .dto.CreateRoleRequest import CreateRoleRequest
from .dto.DeleteRoleResponse import DeleteRoleResponse
from .dto.RoleResponse import RoleResponse
from .dto.UpdateRoleRequest import UpdateRoleRequest
from .RoleService import RoleService


class RoleController(Controller):
    name = ApiLocaleString.from_i18n_path("api.controllers.role.name")
    description = ApiLocaleString.from_i18n_path("api.controllers.role.description")
    icon = "mage:users"

    def __init__(
        self, *, auth: AuthHandler, route: str = "/roles", additionally_required_permission: str | None = None
    ):
        super().__init__(
            auth=auth,
            route=route,
            additionally_required_permission=additionally_required_permission,
        )

    def create_role(self, route: str = "/") -> Self:
        @self.router.post(
            route,
            summary="Create Role",
            description="Creates a new tenant-scoped role with a name, description, and access rules.",
            status_code=status.HTTP_201_CREATED,
            tags=self.tags,
        )
        async def create_role(
            role_data: CreateRoleRequest,
            user: Annotated[
                UserIdentity, Security(self.user_with_permission(f"aihub.admin.service.{self.service_name}"))
            ],
        ) -> RoleResponse:
            try:
                return RoleService.create_role(role_data, user.acting_within_tenant.id)
            except NotUniqueError:
                raise HTTPException(status_code=409, detail=f"Role with name '{role_data.name}' already exists.")
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

        return self

    def get_roles(self, route: str = "/") -> Self:
        @self.router.get(
            route,
            summary="List Roles",
            description="Retrieves all roles available to the current tenant (system + tenant-specific).",
            tags=self.tags,
        )
        async def get_roles(
            user: Annotated[
                UserIdentity, Security(self.user_with_permission(f"aihub.admin.service.{self.service_name}"))
            ],
        ) -> list[RoleResponse]:
            return RoleService.list_roles(user.acting_within_tenant.id)

        return self

    def get_role(self, route: str = "/{role_id}") -> Self:
        @self.router.get(
            route,
            summary="Get Role",
            description="Retrieves a single role by its unique ID.",
            tags=self.tags,
        )
        async def get_role(
            role_id: str,
            user: Annotated[
                UserIdentity, Security(self.user_with_permission(f"aihub.admin.service.{self.service_name}"))
            ],
        ) -> RoleResponse:
            try:
                return RoleService.get_role_by_id(role_id, user.acting_within_tenant.id)
            except DoesNotExist:
                raise HTTPException(status_code=404, detail="Role not found.")

        return self

    def update_role(self, route: str = "/{role_id}") -> Self:
        @self.router.patch(
            route,
            summary="Update Role",
            description="Updates a tenant-scoped role's name, description, or access rules.",
            tags=self.tags,
        )
        async def update_role(
            role_id: str,
            role_data: UpdateRoleRequest,
            user: Annotated[
                UserIdentity, Security(self.user_with_permission(f"aihub.admin.service.{self.service_name}"))
            ],
        ) -> RoleResponse:
            try:
                return RoleService.update_role(role_id, role_data, user.acting_within_tenant.id)
            except DoesNotExist:
                raise HTTPException(status_code=404, detail="Role not found.")
            except NotUniqueError:
                raise HTTPException(status_code=409, detail=f"Role with name '{role_data.name}' already exists.")
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

        return self

    def delete_role(self, route: str = "/{role_id}") -> Self:
        @self.router.delete(
            route,
            summary="Delete Role",
            description="Permanently deletes a tenant-scoped role.",
            tags=self.tags,
        )
        async def delete_role(
            role_id: str,
            user: Annotated[
                UserIdentity, Security(self.user_with_permission(f"aihub.admin.service.{self.service_name}"))
            ],
        ) -> DeleteRoleResponse:
            try:
                RoleService.delete_role(role_id, user.acting_within_tenant.id)
                return DeleteRoleResponse()
            except DoesNotExist:
                raise HTTPException(status_code=404, detail="Role not found.")

        return self
