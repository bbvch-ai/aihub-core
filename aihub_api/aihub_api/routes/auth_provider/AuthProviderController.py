"""Controller for identity provider discovery (unauthenticated)."""

from typing import Self

from aihub_lib.auth.dependencies.AuthHandler import AuthHandler
from aihub_lib.routes.Controller import Controller

from aihub_api.i18n.ApiLocaleString import ApiLocaleString
from aihub_api.routes.auth_provider.AuthProviderService import AuthProviderService
from aihub_api.routes.auth_provider.dto.AuthProviderResponse import AuthProviderResponse


class AuthProviderController(Controller):
    """Exposes available identity providers for the login page.

    This endpoint is unauthenticated because it is called before the user logs in.
    """

    name = ApiLocaleString.from_i18n_path("api.controllers.auth_provider.name")
    description = ApiLocaleString.from_i18n_path("api.controllers.auth_provider.description")
    icon = "mage:shield-check"

    def __init__(
        self, *, auth: AuthHandler, route: str = "/auth-providers", additionally_required_permission: str | None = None
    ):
        super().__init__(auth=auth, route=route, additionally_required_permission=additionally_required_permission)

    def get_auth_providers(self, route: str = "/") -> Self:
        @self.router.get(route, tags=self.tags)
        async def get_auth_providers() -> list[AuthProviderResponse]:
            return await AuthProviderService.get_auth_providers()

        return self
