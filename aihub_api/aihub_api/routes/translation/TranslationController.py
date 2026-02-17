from typing import Annotated, Self

from aihub_lib.auth.dependencies.AuthHandler import AuthHandler
from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.routes.Controller import Controller
from fastapi import Depends, Security

from aihub_api.i18n.ApiLocaleString import ApiLocaleString
from aihub_api.i18n.dependencies.use_locale import use_locale
from aihub_api.routes.translation.dto.TranslationRequest import TranslationRequest
from aihub_api.routes.translation.dto.TranslationResponse import TranslationResponse
from aihub_api.routes.translation.TranslationService import TranslationService


class TranslationController(Controller):
    """
    Controller for handling translation operations using LLM-based translation.

    Provides endpoints to translate LocaleString objects to all supported locales
    (de, en, fr, it) using a single LLM call.
    """

    name = ApiLocaleString.from_i18n_path("api.controllers.translation.name")
    description = ApiLocaleString.from_i18n_path("api.controllers.translation.description")
    icon = "mage:globe"

    def __init__(
        self, *, auth: AuthHandler, route: str = "/translation", additionally_required_permission: str | None = None
    ):
        super().__init__(auth=auth, route=route, additionally_required_permission=additionally_required_permission)

    def translate(self, route: str = "/") -> Self:
        @self.router.post(route, tags=self.tags)
        async def translate_text(
            request: TranslationRequest,
            _: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.?>"))],
            t: Annotated[LocaleHandler, Depends(use_locale)],
        ) -> TranslationResponse:
            """
            Translate a LocaleString to all supported locales.

            Takes a LocaleString with at least one locale populated and translates it
            to all other supported locales (de, en, fr, it) using an LLM.
            """
            return await TranslationService.translate_from_request(request, t)

        return self
