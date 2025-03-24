from typing import TYPE_CHECKING

from aihub_lib.auth.AuthenticatedUser import AuthenticatedUser
from aihub_lib.auth.dependencies.AuthHandler import AuthHandler
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.routes.Controller import Controller
from fastapi import Depends, FastAPI, Security

from aihub_api.i18n.dependencies.use_locale import use_locale
from aihub_api.routes.suite.dto.SuiteDTO import SuiteDTO
from aihub_api.routes.suite.SuiteService import SuiteService

if TYPE_CHECKING:
    from aihub_api.runners.ApiRunner import ApiRunner


class SuiteController(Controller):
    name = LocaleString(en="Suite")
    description = LocaleString(en="Suite endpoints")
    icon = "material-symbols:token"

    def __init__(self, route: str = "/suite", auth: AuthHandler | None = None, is_admin_only=True):
        super().__init__(route, auth, is_admin_only=is_admin_only)
        self._runner: "ApiRunner" | None = None

    def get_suite(self, route: str = "/") -> "SuiteController":
        @self.router.get(route, tags=self.tags)
        async def get_suite(
            user: AuthenticatedUser = Security(self.auth),
            t: LocaleHandler = Depends(use_locale),
        ) -> SuiteDTO:
            return SuiteService.get_suite(user, self._runner, t)

        return self

    def mount(self, app: FastAPI, runner: "ApiRunner"):
        super().mount(app, runner)
        self._runner = runner
