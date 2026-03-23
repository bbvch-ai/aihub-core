from typing import Annotated, Self

from fastapi import Body, Depends, Security
from nats.aio.client import Client as NATS
from swiss_ai_hub.core.auth.dependencies.auth_handler import AuthHandler
from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.dependencies import use_nats
from swiss_ai_hub.core.i18n import LocaleHandler
from swiss_ai_hub.core.routes import Controller

from swiss_ai_hub.api.i18n.api_locale_string import ApiLocaleString
from swiss_ai_hub.api.i18n.dependencies.use_locale import use_locale
from swiss_ai_hub.api.routes.my_account.my_account_service import MyAccountService
from swiss_ai_hub.api.routes.user.dto.dashboard.dashboard_dto import DashboardDTO
from swiss_ai_hub.api.routes.user.dto.user_with_access_dto import UserWithAccessDTO


class MyAccountController(Controller):
    """Endpoints for the logged-in user's own account profile and dashboard."""

    name = ApiLocaleString.from_i18n_path("api.controllers.my_account.name")
    description = ApiLocaleString.from_i18n_path("api.controllers.my_account.description")
    icon = "mage:user"

    def __init__(
        self, *, auth: AuthHandler, route: str = "/my-account", additionally_required_permission: str | None = None
    ):
        super().__init__(auth=auth, route=route, additionally_required_permission=additionally_required_permission)

    def get_my_account(self, route: str = "") -> Self:
        @self.router.get(route, tags=self.tags)
        async def get_my_account(
            nc: Annotated[NATS, Depends(use_nats)],
            t: Annotated[LocaleHandler, Depends(use_locale)],
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.?>"))],
        ) -> UserWithAccessDTO:
            """Returns the currently logged-in user's profile."""
            return await MyAccountService.get_my_account(user, runner=self._runner, nc=nc, t=t)

        return self

    def get_my_dashboard(self, route: str = "/dashboard") -> Self:
        @self.router.get(route, tags=self.tags)
        async def get_my_dashboard(
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.?>"))],
        ) -> DashboardDTO | None:
            """Returns the user's dashboard settings, or null if none exist."""
            return MyAccountService.get_user_dashboard(user)

        return self

    def update_my_dashboard(self, route: str = "/dashboard") -> Self:
        @self.router.put(route, tags=self.tags, status_code=204)
        async def update_my_dashboard(
            dashboard_dto: Annotated[DashboardDTO, Body],
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.?>"))],
        ) -> None:
            """Updates the user's dashboard settings."""
            await MyAccountService.update_user_dashboard(user, dashboard_dto)
            return None

        return self
