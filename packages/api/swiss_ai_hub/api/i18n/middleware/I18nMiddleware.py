import logging
import re

from starlette.datastructures import Headers, QueryParams
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from swiss_ai_hub.core.i18n.LocaleHandler import LocaleHandler

logger = logging.getLogger(__name__)


class I18nMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        locale = self.extract_locale(request.headers, request.path_params, request.query_params)

        logger.debug(f"Setting user locale: {locale}")
        request.state.locale = locale

        return await call_next(request)

    @staticmethod
    def extract_locale(headers: Headers, path_params: dict[str, str], query_params: QueryParams) -> str:
        locale = I18nMiddleware.get_preferred_locale(
            headers.get("lang")
            or headers.get("locale")
            or headers.get("Accept-Language")
            or path_params.get("locale")
            or query_params.get("locale")
            or LocaleHandler.DEFAULT_LOCALE
        )

        if locale not in LocaleHandler.LOCALE_WHITE_LIST:
            locale = LocaleHandler.DEFAULT_LOCALE

        return locale

    @staticmethod
    def get_preferred_locale(accept_language: str) -> str:
        pattern = re.compile(r"^([a-z]{2})", re.IGNORECASE)
        languages = accept_language.split(",")
        for language in languages:
            match = pattern.match(language.strip())
            if match:
                locale = match.group(1).lower()
                return locale
        return LocaleHandler.DEFAULT_LOCALE
