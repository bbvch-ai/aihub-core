import logging
from typing import Annotated, Self

from fastapi import HTTPException, Security, status
from mongoengine.errors import NotUniqueError
from swiss_ai_hub.core.auth.dependencies.auth_handler import AuthHandler
from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.routes import Controller

from swiss_ai_hub.sysadmin_api.i18n import SysadminApiLocaleString
from swiss_ai_hub.sysadmin_api.routes.tenant_admin.dto.create_tenant_metadata_request import CreateTenantMetadataRequest
from swiss_ai_hub.sysadmin_api.routes.tenant_admin.dto.tenant_response import TenantResponse
from swiss_ai_hub.sysadmin_api.routes.tenant_admin.dto.update_tenant_metadata_request import UpdateTenantMetadataRequest
from swiss_ai_hub.sysadmin_api.routes.tenant_admin.tenant_admin_service import TenantAdminService

logger = logging.getLogger(__name__)


class TenantAdminController(Controller):
    """System administrator endpoints for tenant metadata management.

    Not tenant-scoped — these endpoints live at ``/admin/tenants/`` and require
    the ``AIHubSysAdmin`` Keycloak realm role. Manages MongoDB metadata attached to
    existing Keycloak tenant groups. See `TenantAdminService` for the ownership split.
    """

    name = SysadminApiLocaleString.from_i18n_path("sysadmin.controllers.tenant_admin.name")
    description = SysadminApiLocaleString.from_i18n_path("sysadmin.controllers.tenant_admin.description")
    icon = "mage:building-tree"

    _TENANT_ROUTE = "/{tenant_id}"

    def __init__(self, *, auth: AuthHandler, route: str = "/admin/tenants"):
        super().__init__(auth=auth, route=route)

    def list_tenants(self, route: str = "/") -> Self:
        @self.router.get(route, tags=self.tags)
        async def list_tenants(
            _: Annotated[UserIdentity, Security(self.sys_admin_user())],
        ) -> list[TenantResponse]:
            """Lists all tenants: active (Keycloak + metadata) and orphaned (metadata only)."""
            return await TenantAdminService.list_tenants()

        return self

    def list_unconfigured_tenants(self, route: str = "/unconfigured") -> Self:
        @self.router.get(route, tags=self.tags)
        async def list_unconfigured_tenants(
            _: Annotated[UserIdentity, Security(self.sys_admin_user())],
        ) -> list[str]:
            """Lists Keycloak tenant group names that don't yet have metadata configured."""
            return await TenantAdminService.list_unconfigured_tenant_ids()

        return self

    def get_tenant(self, route: str = _TENANT_ROUTE) -> Self:
        @self.router.get(route, tags=self.tags)
        async def get_tenant(
            tenant_id: str,
            _: Annotated[UserIdentity, Security(self.sys_admin_user())],
        ) -> TenantResponse:
            """Retrieves a single tenant by its ID."""
            return await TenantAdminService.get_tenant(tenant_id)

        return self

    def create_tenant_metadata(self, route: str = "/") -> Self:
        @self.router.post(route, status_code=status.HTTP_201_CREATED, tags=self.tags)
        async def create_tenant_metadata(
            data: CreateTenantMetadataRequest,
            _: Annotated[UserIdentity, Security(self.sys_admin_user())],
        ) -> TenantResponse:
            """Attaches metadata (name, description, access rules) to an existing Keycloak tenant group."""
            try:
                return await TenantAdminService.create_tenant_metadata(data)
            except NotUniqueError:
                raise HTTPException(status_code=409, detail=f"Tenant with name '{data.name}' already exists.")

        return self

    def update_tenant_metadata(self, route: str = _TENANT_ROUTE) -> Self:
        @self.router.patch(route, tags=self.tags)
        async def update_tenant_metadata(
            tenant_id: str,
            data: UpdateTenantMetadataRequest,
            _: Annotated[UserIdentity, Security(self.sys_admin_user())],
        ) -> TenantResponse:
            """Updates a tenant's name, description, or access rules. Not allowed on orphaned tenants."""
            try:
                return await TenantAdminService.update_tenant_metadata(tenant_id, data)
            except NotUniqueError:
                raise HTTPException(status_code=409, detail=f"Tenant with name '{data.name}' already exists.")

        return self

    def delete_tenant_metadata(self, route: str = _TENANT_ROUTE) -> Self:
        @self.router.delete(route, status_code=status.HTTP_204_NO_CONTENT, tags=self.tags)
        async def delete_tenant_metadata(
            tenant_id: str,
            _: Annotated[UserIdentity, Security(self.sys_admin_user())],
        ) -> None:
            """Removes the MongoDB metadata for the tenant. Allowed on both active and orphaned rows.

            The Keycloak group (if present) is not touched — manage it in the Keycloak admin console.
            The last remaining tenant cannot be deleted (409); any tenant may be deleted as long as at
            least one other tenant exists.
            """
            await TenantAdminService.delete_tenant_metadata(tenant_id)

        return self
