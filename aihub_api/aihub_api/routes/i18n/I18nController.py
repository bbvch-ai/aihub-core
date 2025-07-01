from typing import Annotated

from aihub_lib.auth.dependencies.AuthHandler import AuthHandler
from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.routes.Controller import Controller
from fastapi import Depends, Security

from aihub_api.i18n.dependencies.use_locale import use_locale
from aihub_api.routes.i18n.dto.LocaleResponse import LocaleResponse
from aihub_api.routes.i18n.I18nService import I18nService


class I18nController(Controller):
    """
    A controller for handling internationalization (i18n) operations, such as retrieving the user's current locale.

    ### Why I18nController?
    In a multi-language environment, it's often useful to provide endpoints that reflect the user’s language
    preferences. The `I18nController` exposes endpoints that:
    - Detect the user’s current locale (e.g., from headers, user profile, or query parameters).
    - Return test strings in the detected language, verifying that translations and locale handling are working properly.
    """

    name = LocaleString(en="Localization")
    description = LocaleString(en="Localization service")
    icon = "mdi:language"

    def __init__(self, *, auth: AuthHandler, route: str = "/i18n"):
        super().__init__(auth=auth, route=route)

    def get_my_locale(self, route: str = "/my-locale") -> "I18nController":
        @self.router.get(route, tags=self.tags)
        async def get_locale(
            _: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.?>"))],
            t: Annotated[LocaleHandler, Depends(use_locale)],
        ) -> LocaleResponse:
            """
            Return the user's current locale and a localized test string.
            """
            return I18nService.get_user_locale(t)

        return self
