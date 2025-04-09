import logging
import re

from aihub_lib.i18n.LocaleHandler import LocaleHandler
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request

logger = logging.getLogger(__name__)

class I18nMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        locale = self.get_preferred_locale(
            request.headers.get("lang", None)
            or request.headers.get("locale", None)
            or request.headers.get("Accept-Language", None)
            or request.path_params.get("locale", None)
            or request.query_params.get("locale", None)
            or LocaleHandler.DEFAULT_LOCALE
        )

        if locale not in LocaleHandler.LOCALE_WHITE_LIST:
            locale = LocaleHandler.DEFAULT_LOCALE

        logger.debug(f"Setting user locale: {locale}")
        request.state.locale = locale

        return await call_next(request)

    def get_preferred_locale(self, accept_language: str) -> str:
        pattern = re.compile(r"^([a-z]{2})", re.IGNORECASE)
        languages = accept_language.split(",")
        for language in languages:
            match = pattern.match(language.strip())
            if match:
                locale = match.group(1).lower()
                return locale
        return LocaleHandler.DEFAULT_LOCALE
