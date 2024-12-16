from typing import Callable, Any

from fastapi import APIRouter, Depends

from api_core.i18n.dependencies.use_locale import use_locale
from api_core.routes.Controller import Controller
from api_core.routes.i18n.dto.LocaleResponse import LocaleResponse
from api_core.routes.i18n.I18nService import I18nService
from lib_core.i18n.LocaleHandler import LocaleHandler
from lib_core.records.User import User

class I18nController(Controller):

    def __init__(self, route: str = "/i18n", user_auth_strategy: Callable[..., Any] = None):
        super().__init__(route, user_auth_strategy)

    def get_my_locale(self, route: str = "/my-locale") -> "I18nController":
        @self.router.get(
            route,
            summary="Get User Locale",
            description="Retrieves the current locale (language) setting for the user's session. This endpoint also returns a test string in the detected language.",
            tags=["Utility"],
            responses={
                200: {"description": "Successful response with user locale information"},
            },
        )
        async def get_locale(
                user: User = Depends(self.user_auth_strategy),
                t: LocaleHandler = Depends(use_locale),
        ) -> LocaleResponse:
            return I18nService.get_user_locale(user, t)

        return self