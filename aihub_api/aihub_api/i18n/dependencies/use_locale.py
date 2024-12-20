from fastapi import Request

from aihub_api.i18n.ApiLocaleHandler import ApiLocaleHandler


async def use_locale(request: Request) -> ApiLocaleHandler:
    return ApiLocaleHandler(locale=request.state.locale)