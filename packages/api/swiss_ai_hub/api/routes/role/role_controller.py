import logging
from typing import Annotated, Self

from fastapi import Depends, HTTPException, Request, Security, status
from mongoengine.errors import NotUniqueError
from swiss_ai_hub.core.auth.access.access_checker import AccessChecker
from swiss_ai_hub.core.auth.dependencies.auth_handler import AuthHandler
from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.i18n import LocaleHandler
from swiss_ai_hub.core.routes import TenantScopedController

from swiss_ai_hub.api.i18n.api_locale_string import ApiLocaleString
from swiss_ai_hub.api.i18n.dependencies.use_locale import use_locale
from swiss_ai_hub.api.routes.access.access_capability_service import AccessCapabilityService
from swiss_ai_hub.api.routes.access.access_preset_service import AccessPresetService
from swiss_ai_hub.api.routes.access.dto.access_capabilities_dto import AccessCapabilitiesResponse
from swiss_ai_hub.api.routes.access.dto.access_capabilities_request import AccessCapabilitiesRequest
from swiss_ai_hub.api.routes.access.dto.access_preset_dto import AccessPresetDTO
from swiss_ai_hub.api.routes.access.platform_access_proxy import PlatformAccessProxy

from .dto.create_role_request import CreateRoleRequest
from .dto.delete_role_response import DeleteRoleResponse
from .dto.role_response import RoleResponse
from .dto.update_role_request import UpdateRoleRequest
from .role_service import RoleService

logger = logging.getLogger(__name__)


class RoleController(TenantScopedController):
    name = ApiLocaleString.from_i18n_path("api.controllers.role.name")
    description = ApiLocaleString.from_i18n_path("api.controllers.role.description")
    icon = "mage:security-shield"

    _ROLE_ID_ROUTE = "/{role_id}"

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
            except HTTPException:
                raise
            except Exception as e:
                logger.exception("Unexpected error creating role")
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

    def get_role(self, route: str = _ROLE_ID_ROUTE) -> Self:
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
            return RoleService.get_role_by_id(role_id, user.acting_within_tenant.id)

        return self

    def update_role(self, route: str = _ROLE_ID_ROUTE) -> Self:
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
            except NotUniqueError:
                raise HTTPException(status_code=409, detail=f"Role with name '{role_data.name}' already exists.")
            except HTTPException:
                raise
            except Exception as e:
                logger.exception("Unexpected error updating role")
                raise HTTPException(status_code=400, detail=str(e))

        return self

    def delete_role(self, route: str = _ROLE_ID_ROUTE) -> Self:
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
            RoleService.delete_role(role_id, user.acting_within_tenant.id)
            return DeleteRoleResponse()

        return self

    def get_access_capabilities(self, route: str = "/access/capabilities") -> Self:
        @self.router.post(
            route,
            summary="Evaluate Access Capabilities",
            description="Returns the catalog of concrete capabilities (per service, agent and process), each with "
            "its exact access rule and whether the supplied draft rules grant it.",
            tags=self.tags,
        )
        async def get_access_capabilities(
            request: AccessCapabilitiesRequest,
            http_request: Request,
            user: Annotated[
                UserIdentity, Security(self.user_with_permission(f"aihub.admin.service.{self.service_name}"))
            ],
            t: Annotated[LocaleHandler, Depends(use_locale)],
        ) -> AccessCapabilitiesResponse:
            platform_api_base_url = self._runner.platform_api_base_url
            if platform_api_base_url is not None:
                return await PlatformAccessProxy.fetch_capabilities(
                    platform_api_base_url, http_request.path_params["tenant_id"], http_request, request
                )
            subject = AccessChecker(
                user_access_rules=request.access_rules,
                tenant_access_rules=request.access_rules,
                is_sys_admin=request.is_sys_admin,
            )
            ceiling = None
            if request.restrict_to_tenant:
                tenant_rules = user.acting_within_tenant.access_rules
                ceiling = AccessChecker(user_access_rules=tenant_rules, tenant_access_rules=tenant_rules)
            return await AccessCapabilityService.build_capabilities(subject, self._runner, t, ceiling)

        return self

    def get_access_presets(self, route: str = "/access/presets") -> Self:
        @self.router.get(
            route,
            summary="List Access Presets",
            description="Returns a curated, described library of common access rules for one-click authoring.",
            tags=self.tags,
        )
        async def get_access_presets(
            http_request: Request,
            _: Annotated[UserIdentity, Security(self.user_with_permission(f"aihub.admin.service.{self.service_name}"))],
            t: Annotated[LocaleHandler, Depends(use_locale)],
        ) -> list[AccessPresetDTO]:
            platform_api_base_url = self._runner.platform_api_base_url
            if platform_api_base_url is not None:
                return await PlatformAccessProxy.fetch_presets(
                    platform_api_base_url, http_request.path_params["tenant_id"], http_request
                )
            return AccessPresetService.get_presets(t)

        return self
