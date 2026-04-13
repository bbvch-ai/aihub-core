import logging
from typing import Annotated, Self

from fastapi import Depends, HTTPException, status
from mongoengine.errors import NotUniqueError
from swiss_ai_hub.core.auth.dependencies.auth_handler import AuthHandler
from swiss_ai_hub.core.auth.dependencies.sys_admin_auth_handler.sys_admin_auth_handler import SysAdminAuthHandler
from swiss_ai_hub.core.auth.identity.sys_admin_identity import SysAdminIdentity
from swiss_ai_hub.core.routes import Controller

from swiss_ai_hub.api.i18n.api_locale_string import ApiLocaleString
from swiss_ai_hub.api.routes.tenant_admin.dto.create_tenant_request import CreateTenantRequest
from swiss_ai_hub.api.routes.tenant_admin.dto.tenant_response import TenantResponse
from swiss_ai_hub.api.routes.tenant_admin.dto.update_tenant_request import UpdateTenantRequest
from swiss_ai_hub.api.routes.tenant_admin.tenant_admin_service import TenantAdminService

logger = logging.getLogger(__name__)


class TenantAdminController(Controller):
    """System administrator endpoints for tenant CRUD operations.

    Not tenant-scoped — these endpoints live at ``/admin/tenants/`` and require
    the ``AIHubSysAdmin`` Keycloak realm role.
    """

    name = ApiLocaleString.from_i18n_path("api.controllers.tenant_admin.name")
    description = ApiLocaleString.from_i18n_path("api.controllers.tenant_admin.description")
    icon = "mage:building-tree"

    def __init__(
        self, *, auth: AuthHandler, route: str = "/admin/tenants", additionally_required_permission: str | None = None
    ):
        super().__init__(auth=auth, route=route, additionally_required_permission=additionally_required_permission)
        self._sys_admin_auth = SysAdminAuthHandler()

    def list_tenants(self, route: str = "/") -> Self:
        @self.router.get(
            route,
            summary="List Tenants",
            description="Lists all tenants in the system.",
            tags=self.tags,
        )
        async def list_tenants(
            identity: Annotated[SysAdminIdentity, Depends(self._sys_admin_auth)],
        ) -> list[TenantResponse]:
            return TenantAdminService.list_tenants()

        return self

    def get_tenant(self, route: str = "/{tenant_id}") -> Self:
        @self.router.get(
            route,
            summary="Get Tenant",
            description="Retrieves a single tenant by its ID.",
            tags=self.tags,
        )
        async def get_tenant(
            tenant_id: str,
            identity: Annotated[SysAdminIdentity, Depends(self._sys_admin_auth)],
        ) -> TenantResponse:
            return TenantAdminService.get_tenant(tenant_id)

        return self

    def create_tenant(self, route: str = "/") -> Self:
        @self.router.post(
            route,
            summary="Create Tenant",
            description="Creates a new tenant with a name, description, and access rules.",
            status_code=status.HTTP_201_CREATED,
            tags=self.tags,
        )
        async def create_tenant(
            data: CreateTenantRequest,
            identity: Annotated[SysAdminIdentity, Depends(self._sys_admin_auth)],
        ) -> TenantResponse:
            try:
                return TenantAdminService.create_tenant(data)
            except NotUniqueError:
                raise HTTPException(status_code=409, detail=f"Tenant with name '{data.name}' already exists.")

        return self

    def update_tenant(self, route: str = "/{tenant_id}") -> Self:
        @self.router.patch(
            route,
            summary="Update Tenant",
            description="Updates a tenant's name, description, or access rules.",
            tags=self.tags,
        )
        async def update_tenant(
            tenant_id: str,
            data: UpdateTenantRequest,
            identity: Annotated[SysAdminIdentity, Depends(self._sys_admin_auth)],
        ) -> TenantResponse:
            try:
                return TenantAdminService.update_tenant(tenant_id, data)
            except NotUniqueError:
                raise HTTPException(status_code=409, detail=f"Tenant with name '{data.name}' already exists.")

        return self

    def delete_tenant(self, route: str = "/{tenant_id}") -> Self:
        @self.router.delete(
            route,
            summary="Delete Tenant",
            description="Permanently deletes a tenant and all associated data. The default tenant cannot be deleted.",
            status_code=status.HTTP_204_NO_CONTENT,
            tags=self.tags,
        )
        async def delete_tenant(
            tenant_id: str,
            identity: Annotated[SysAdminIdentity, Depends(self._sys_admin_auth)],
        ) -> None:
            TenantAdminService.delete_tenant(tenant_id)

        return self
