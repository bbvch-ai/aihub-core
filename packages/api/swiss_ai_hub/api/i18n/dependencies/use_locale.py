from fastapi import Request, WebSocket

from swiss_ai_hub.api.i18n.api_locale_handler import ApiLocaleHandler
from swiss_ai_hub.api.i18n.middleware.i18n_middleware import I18nMiddleware


async def use_locale(request: Request) -> ApiLocaleHandler:
    return ApiLocaleHandler(locale=request.state.locale)


async def use_locale_ws(request: WebSocket) -> ApiLocaleHandler:
    locale = I18nMiddleware.extract_locale(request.headers, request.path_params, request.query_params)
    return ApiLocaleHandler(locale=locale)
