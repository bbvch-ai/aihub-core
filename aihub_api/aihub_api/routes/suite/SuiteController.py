from typing import TYPE_CHECKING, Annotated, Optional

from aihub_lib.auth.dependencies.AuthHandler import AuthHandler
from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.routes.Controller import Controller
from fastapi import Depends, FastAPI, Security
from typing_extensions import override

from aihub_api.i18n.dependencies.use_locale import use_locale
from aihub_api.routes.suite.dto.SuiteDTO import SuiteDTO
from aihub_api.routes.suite.SuiteService import SuiteService

if TYPE_CHECKING:
    from aihub_api.runners.ApiRunner import ApiRunner


class SuiteController(Controller):
    name = LocaleString(en="Suite")
    description = LocaleString(en="Suite endpoints")
    icon = "material-symbols:token"

    def __init__(self, *, auth: AuthHandler, route: str = "/suites"):
        super().__init__(auth=auth, route=route)
        self._runner: Optional["ApiRunner"] = None

    def get_suite(self, route: str = "/") -> "SuiteController":
        @self.router.get(route, tags=self.tags)
        async def get_suite(
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.?>"))],
            t: Annotated[LocaleHandler, Depends(use_locale)],
        ) -> SuiteDTO:
            return SuiteService.get_suite(user, self._runner, t)

        return self

    @override
    def mount(self, app: FastAPI, runner: "ApiRunner"):
        super().mount(app, runner)
        self._runner = runner
