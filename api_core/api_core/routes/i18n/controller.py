from typing import Callable, Any

from fastapi import APIRouter, Depends

from api_core.i18n.dependencies.use_locale import use_locale
from api_core.routes.i18n.dto.LocaleResponse import LocaleResponse
from api_core.routes.i18n.service import get_user_locale
from lib_core.i18n.LocaleHandler import LocaleHandler
from lib_core.records.User import User

def i18n_controller_factory(user_auth_strategy: Callable[..., Any]):
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
        t: LocaleHandler = Depends(use_locale),
    ) -> LocaleResponse:
        # Delegate logic to the service layer
        return get_user_locale(user, t)

    return i18n_router
