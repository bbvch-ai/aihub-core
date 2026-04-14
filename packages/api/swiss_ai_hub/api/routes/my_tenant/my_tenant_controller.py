from typing import Annotated, Self

from fastapi import Body, Security
from swiss_ai_hub.core.auth.dependencies.auth_handler import AuthHandler
from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.routes import Controller

from swiss_ai_hub.api.i18n.api_locale_string import ApiLocaleString
from swiss_ai_hub.api.routes.my_tenant.dto.active_tenant_dto import ActiveTenantDTO
from swiss_ai_hub.api.routes.my_tenant.dto.set_active_tenant_request import SetActiveTenantRequest
from swiss_ai_hub.api.routes.my_tenant.dto.tenant_membership_dto import TenantMembershipDTO
from swiss_ai_hub.api.routes.my_tenant.my_tenant_service import MyTenantService


class MyTenantController(Controller):
    """Global endpoints for managing the logged-in user's tenant context.

    Not tenant-scoped — these endpoints live at ``/my-tenants/`` without a ``{tenant_id}`` prefix.
    """

    name = ApiLocaleString.from_i18n_path("api.controllers.my_tenant.name")
    description = ApiLocaleString.from_i18n_path("api.controllers.my_tenant.description")
    icon = "mage:building"

    def __init__(
        self, *, auth: AuthHandler, route: str = "/my-tenants", additionally_required_permission: str | None = None
    ):
        super().__init__(auth=auth, route=route, additionally_required_permission=additionally_required_permission)

    def get_my_tenants(self, route: str = "") -> Self:
        @self.router.get(route, tags=self.tags)
        async def get_my_tenants(
            user: Annotated[UserIdentity, Security(self.authenticated_user())],
        ) -> list[TenantMembershipDTO]:
            """Returns all tenants the current user belongs to."""
            return MyTenantService.get_my_tenants(user.id)

        return self

    def get_my_active_tenant(self, route: str = "/active") -> Self:
        @self.router.get(route, tags=self.tags)
        async def get_my_active_tenant(
            user: Annotated[UserIdentity, Security(self.authenticated_user())],
        ) -> ActiveTenantDTO:
            """Returns the current user's active tenant."""
            return await MyTenantService.get_my_active_tenant(user.id)

        return self

    def set_my_active_tenant(self, route: str = "/active") -> Self:
        @self.router.put(route, tags=self.tags)
        async def set_my_active_tenant(
            request_body: Annotated[SetActiveTenantRequest, Body],
            user: Annotated[UserIdentity, Security(self.authenticated_user())],
        ) -> ActiveTenantDTO:
            """Sets the current user's active tenant."""
            return await MyTenantService.set_my_active_tenant(user.id, request_body.tenant_id)

        return self
