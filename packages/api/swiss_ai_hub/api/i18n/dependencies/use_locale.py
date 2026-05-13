from fastapi import Request, WebSocket
from swiss_ai_hub.core.i18n import LocaleHandler

from swiss_ai_hub.api.i18n.api_locale_handler import ApiLocaleHandler
from swiss_ai_hub.api.i18n.middleware.i18n_middleware import I18nMiddleware


async def use_locale(request: Request) -> ApiLocaleHandler:
    """Resolves the effective locale for the current request.

    Header-driven `lang`/`locale` always wins (Admin UI sends one per request). When no explicit
    header is present, fall back to the authenticated user's persisted `preferred_locale` —
    this is the case for OpenWebUI pipeline calls. Last resort: middleware-extracted value.

    Requires the authenticating Security dependency to be declared before `Depends(use_locale)`
    in the route signature so `request.state.user` is set in time. AuthHandler.build_identity
    attaches the identity there.
    """
    if request.state.locale_is_explicit:
        return ApiLocaleHandler(locale=request.state.locale)

    user = getattr(request.state, "user", None)
    if user is not None and user.preferred_locale in LocaleHandler.LOCALE_WHITE_LIST:
        return ApiLocaleHandler(locale=user.preferred_locale)

    return ApiLocaleHandler(locale=request.state.locale)


async def use_locale_ws(request: WebSocket) -> ApiLocaleHandler:
    locale = I18nMiddleware.extract_locale(request.headers, request.path_params, request.query_params)
    user = getattr(request.state, "user", None)
    if user is not None and user.preferred_locale in LocaleHandler.LOCALE_WHITE_LIST:
        locale = user.preferred_locale
    return ApiLocaleHandler(locale=locale)
