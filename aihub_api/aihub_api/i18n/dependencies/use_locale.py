from fastapi import Request, WebSocket

from aihub_api.i18n.ApiLocaleHandler import ApiLocaleHandler


async def use_locale(request: Request) -> ApiLocaleHandler:
    return ApiLocaleHandler(locale=request.state.locale)


async def use_locale_ws(request: WebSocket) -> ApiLocaleHandler:
    return ApiLocaleHandler(locale=request.state.locale)
