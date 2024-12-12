from typing import Callable, Any

from fastapi import APIRouter, Request, Depends

from api_core.i18n.dependencies.use_locale import use_locale
from api_core.routes.i18n.dto.LocaleResponse import LocaleResponse
from lib_core.i18n.LocaleHandler import LocaleHandler
from lib_core.records.User import User


def i18n_controller_factory(user_auth_strategy:  Callable[..., Any]):
    i18n_router = APIRouter()

    @i18n_router.get(
        "/locale",
        summary="Get User Locale",
        description="Retrieves the current locale (language) setting for the user's session. This endpoint also returns a test string in the detected language.",
        tags=["Utility"],
        responses={
            200: {"description": "Successful response with user locale information"},
        },
    )
    async def get_locale(
            user: User = Depends(user_auth_strategy),
            t: LocaleHandler = Depends(use_locale)
    ) -> LocaleResponse:
        return LocaleResponse(lang=t.locale, test=t("api.common.test"))

    return i18n_router