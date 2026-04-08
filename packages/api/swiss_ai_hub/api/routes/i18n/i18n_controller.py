from typing import Annotated, Self

from fastapi import Depends, Security
from swiss_ai_hub.core.auth.dependencies.auth_handler import AuthHandler
from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.i18n import LocaleHandler
from swiss_ai_hub.core.routes import TenantScopedController

from swiss_ai_hub.api.i18n.api_locale_string import ApiLocaleString
from swiss_ai_hub.api.i18n.dependencies.use_locale import use_locale
from swiss_ai_hub.api.routes.i18n.dto.locale_response import LocaleResponse
from swiss_ai_hub.api.routes.i18n.i18n_service import I18nService


class I18nController(TenantScopedController):
    """
    A controller for handling internationalization (i18n) operations, such as retrieving the user's current locale.

    ### Why I18nController?
    In a multi-language environment, it's often useful to provide endpoints that reflect the user’s language
    preferences. The `I18nController` exposes endpoints that:
    - Detect the user’s current locale (e.g., from headers, user profile, or query parameters).
    - Return test strings in the detected language, verifying that translations and locale
      handling are working properly.
    """

    name = ApiLocaleString.from_i18n_path("api.controllers.i18n.name")
    description = ApiLocaleString.from_i18n_path("api.controllers.i18n.description")
    icon = "mage:globe"

    def __init__(self, *, auth: AuthHandler, route: str = "/i18n", additionally_required_permission: str | None = None):
        super().__init__(auth=auth, route=route, additionally_required_permission=additionally_required_permission)

    def get_my_locale(self, route: str = "/my-locale") -> Self:
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
