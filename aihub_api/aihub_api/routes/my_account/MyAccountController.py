from typing import Annotated

from aihub_lib.auth.dependencies.AuthHandler import AuthHandler
from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.dependencies.use_nats import use_nats
from aihub_lib.routes.Controller import Controller
from fastapi import Body, Depends, Security
from nats.aio.client import Client as NATS

from aihub_api.i18n.dependencies.use_locale import use_locale
from aihub_api.routes.my_account.MyAccountService import MyAccountService
from aihub_api.routes.user.dto.Dashboard.DashboardDTO import DashboardDTO
from aihub_api.routes.user.dto.UserWithAccessDTO import UserWithAccessDTO


class MyAccountController(Controller):
    """
    Controller for personal account management.

    Provides endpoints for authenticated users to view and manage their own profile,
    dashboard settings, and account information.
    """

    name = LocaleString(en="My Account", de="Mein Konto", fr="Mon compte", it="Il mio account")
    description = LocaleString(
        en="Manage your account settings",
        de="Kontoeinstellungen verwalten",
        fr="Gérez les paramètres de votre compte",
        it="Gestisci le impostazioni del tuo account",
    )
    icon = "mdi:account"

    def __init__(
        self, *, auth: AuthHandler, route: str = "/my-account", additionally_required_permission: str | None = None
    ):
        super().__init__(auth=auth, route=route, additionally_required_permission=additionally_required_permission)

    def get_my_account(self, route: str = "/") -> "MyAccountController":
        """
        Registers an endpoint to retrieve the currently logged-in user's account info.
        """

        @self.router.get(route, tags=self.tags)
        async def get_my_account(
            nc: Annotated[NATS, Depends(use_nats)],
            t: Annotated[LocaleHandler, Depends(use_locale)],
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.?>"))],
        ) -> UserWithAccessDTO:
            """
            Returns the currently logged-in user's account information including access permissions.
            """
            return await MyAccountService.get_logged_in_user(user, runner=self._runner, nc=nc, t=t)

        return self

    def get_my_dashboard(self, route: str = "/dashboard") -> "MyAccountController":
        """
        Registers an endpoint to retrieve the currently logged-in user's dashboard settings.
        """

        @self.router.get(route, tags=self.tags)
        async def get_my_dashboard(
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.?>"))],
        ) -> DashboardDTO | None:
            """
            Returns the user's dashboard settings, or null if none exist.
            """
            return MyAccountService.get_user_dashboard(user)

        return self

    def update_my_dashboard(self, route: str = "/dashboard") -> "MyAccountController":
        """
        Registers an endpoint to update the currently logged-in user's dashboard settings.
        """

        @self.router.put(route, tags=self.tags, status_code=204)
        async def update_my_dashboard(
            dashboard_dto: Annotated[DashboardDTO, Body],
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.?>"))],
        ) -> None:
            """
            Updates the user's dashboard settings.
            """
            await MyAccountService.update_user_dashboard(user, dashboard_dto)

        return self
