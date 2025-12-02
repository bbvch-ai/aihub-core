from typing import Annotated

from aihub_lib.auth.dependencies.AuthHandler import AuthHandler
from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.routes.Controller import Controller
from fastapi import Depends, Security

from aihub_api.i18n.dependencies.use_locale import use_locale
from aihub_api.routes.suite.dto.SuiteDTO import SuiteDTO
from aihub_api.routes.suite.SuiteService import SuiteService


class SuiteController(Controller):
    name = LocaleString(en="Platform Overview", de="Plattformübersicht", fr="Vue d'ensemble de la plateforme", it="Panoramica della piattaforma")
    description = LocaleString(en="View platform features and settings", de="Plattformfunktionen und Einstellungen anzeigen", fr="Consultez les fonctionnalités et paramètres de la plateforme", it="Visualizza funzionalità e impostazioni della piattaforma")
    icon = "material-symbols:token"

    def __init__(
        self, *, auth: AuthHandler, route: str = "/suites", additionally_required_permission: str | None = None
    ):
        super().__init__(auth=auth, route=route, additionally_required_permission=additionally_required_permission)

    def get_suite(self, route: str = "/") -> "SuiteController":
        @self.router.get(route, tags=self.tags)
        async def get_suite(
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.?>"))],
            t: Annotated[LocaleHandler, Depends(use_locale)],
        ) -> SuiteDTO:
            return SuiteService.get_suite(user, self._runner, t)

        return self
