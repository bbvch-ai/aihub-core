from fastapi import Request, WebSocket

from swiss_ai_hub.api.i18n.ApiLocaleHandler import ApiLocaleHandler
from swiss_ai_hub.api.i18n.middleware.I18nMiddleware import I18nMiddleware


async def use_locale(request: Request) -> ApiLocaleHandler:
    return ApiLocaleHandler(locale=request.state.locale)


async def use_locale_ws(request: WebSocket) -> ApiLocaleHandler:
    locale = I18nMiddleware.extract_locale(request.headers, request.path_params, request.query_params)
    return ApiLocaleHandler(locale=locale)
