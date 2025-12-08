from typing import Annotated

from aihub_lib.auth.access.AccessChecker import AccessChecker
from aihub_lib.auth.dependencies.AuthHandler import AuthHandler
from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.routes.Controller import Controller
from fastapi import HTTPException, Security, status
from mongoengine.errors import DoesNotExist, NotUniqueError

from .dto.CreateRoleRequest import CreateRoleRequest
from .dto.DeleteRoleResponse import DeleteRoleResponse
from .dto.RoleResponse import RoleResponse
from .dto.UpdateRoleRequest import UpdateRoleRequest
from .RoleService import RoleService


class RoleController(Controller):
    name = LocaleString(en="User Roles", de="Benutzerrollen", fr="Rôles d'utilisateur", it="Ruoli utente")
    description = LocaleString(
        en="Configure access permissions and roles",
        de="Zugriffsrechte und Rollen konfigurieren",
        fr="Configurez les autorisations d'accès et les rôles",
        it="Configura permessi di accesso e ruoli",
    )
    icon = "solar:users-group-rounded-bold"

    def __init__(
        self, *, auth: AuthHandler, route: str = "/roles", additionally_required_permission: str | None = None
    ):
        super().__init__(
            auth=auth,
            route=route,
            additionally_required_permission=additionally_required_permission,
        )

    def create_role(self, route: str = "/") -> "RoleController":
        @self.router.post(
            route,
            summary="Create Role",
            description="Creates a new role with a name, description, and access rules.",
            status_code=status.HTTP_201_CREATED,
            tags=self.tags,
        )
        async def create_role(
            role_data: CreateRoleRequest,
            _: Annotated[UserIdentity, Security(self.user_with_permission(f"aihub.admin.service.{self.service_name}"))],
        ) -> RoleResponse:
            try:
                for rule in role_data.access_rules:
                    if not AccessChecker.validate_user_access_rule(rule):
                        raise HTTPException(
                            status_code=400,
                            detail=f"Invalid access rule: {rule}. "
                            f"Access rules must be in the format <resource>.<action>.",
                        )
                return RoleService.create_role(role_data)
            except NotUniqueError:
                raise HTTPException(status_code=409, detail=f"Role with name '{role_data.name}' already exists.")
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

        return self

    def get_roles(self, route: str = "/") -> "RoleController":
        @self.router.get(
            route,
            summary="List Roles",
            description="Retrieves a list of all available roles.",
            tags=self.tags,
        )
        async def get_roles(
            _: Annotated[UserIdentity, Security(self.user_with_permission(f"aihub.admin.service.{self.service_name}"))],
        ) -> list[RoleResponse]:
            return RoleService.list_roles()

        return self

    def get_role(self, route: str = "/{role_id}") -> "RoleController":
        @self.router.get(
            route,
            summary="Get Role",
            description="Retrieves a single role by its unique ID.",
            tags=self.tags,
        )
        async def get_role(
            role_id: str,
            _: Annotated[UserIdentity, Security(self.user_with_permission(f"aihub.admin.service.{self.service_name}"))],
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
        async def update_role(
            role_id: str,
            role_data: UpdateRoleRequest,
            _: Annotated[UserIdentity, Security(self.user_with_permission(f"aihub.admin.service.{self.service_name}"))],
        ) -> RoleResponse:
            try:
                for rule in role_data.access_rules:
                    if not AccessChecker.validate_user_access_rule(rule):
                        raise HTTPException(
                            status_code=400,
                            detail=f"Invalid access rule: {rule}.",
                        )
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
        async def delete_role(
            role_id: str,
            _: Annotated[UserIdentity, Security(self.user_with_permission(f"aihub.admin.service.{self.service_name}"))],
        ) -> DeleteRoleResponse:
            try:
                RoleService.delete_role(role_id)
                return DeleteRoleResponse()
            except DoesNotExist:
                raise HTTPException(status_code=404, detail="Role not found.")

        return self
