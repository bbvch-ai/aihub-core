from typing import Annotated, Self

from fastapi import Depends, Security
from swiss_ai_hub.core.auth.dependencies.AuthHandler import AuthHandler
from swiss_ai_hub.core.auth.identity.UserIdentity import UserIdentity
from swiss_ai_hub.core.i18n.LocaleHandler import LocaleHandler
from swiss_ai_hub.core.routes.Controller import Controller

from swiss_ai_hub.api.i18n.ApiLocaleString import ApiLocaleString
from swiss_ai_hub.api.i18n.dependencies.use_locale import use_locale
from swiss_ai_hub.api.routes.suite.dto.SuiteDTO import SuiteDTO
from swiss_ai_hub.api.routes.suite.SuiteService import SuiteService


class SuiteController(Controller):
    name = ApiLocaleString.from_i18n_path("api.controllers.suite.name")
    description = ApiLocaleString.from_i18n_path("api.controllers.suite.description")
    icon = "mage:coin-a"

    def __init__(
        self, *, auth: AuthHandler, route: str = "/suites", additionally_required_permission: str | None = None
    ):
        super().__init__(auth=auth, route=route, additionally_required_permission=additionally_required_permission)

    def get_suite(self, route: str = "/") -> Self:
        @self.router.get(route, tags=self.tags)
        async def get_suite(
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.?>"))],
            t: Annotated[LocaleHandler, Depends(use_locale)],
        ) -> SuiteDTO:
            return SuiteService.get_suite(user, self._runner, t)

        return self
