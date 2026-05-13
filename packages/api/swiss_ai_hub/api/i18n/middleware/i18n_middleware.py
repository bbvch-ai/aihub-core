import logging
import re

from starlette.datastructures import Headers, QueryParams
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from swiss_ai_hub.core.i18n import LocaleHandler

logger = logging.getLogger(__name__)


class I18nMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        locale, is_explicit = self.extract_locale_with_source(
            request.headers, request.path_params, request.query_params
        )

        logger.debug(f"Setting user locale: {locale} (explicit={is_explicit})")
        request.state.locale = locale
        request.state.locale_is_explicit = is_explicit

        return await call_next(request)

    @staticmethod
    def extract_locale(headers: Headers, path_params: dict[str, str], query_params: QueryParams) -> str:
        locale, _ = I18nMiddleware.extract_locale_with_source(headers, path_params, query_params)
        return locale

    @staticmethod
    def extract_locale_with_source(
        headers: Headers, path_params: dict[str, str], query_params: QueryParams
    ) -> tuple[str, bool]:
        """Resolves the locale and reports whether it came from an explicit `lang`/`locale` header.

        An explicit header signals the client wants a specific locale for this request and should
        take precedence over the user's persisted ``preferred_locale``.
        """
        explicit = headers.get("lang") or headers.get("locale")
        if explicit:
            return I18nMiddleware.get_preferred_locale(explicit), True

        fallback = (
            headers.get("Accept-Language")
            or path_params.get("locale")
            or query_params.get("locale")
            or LocaleHandler.DEFAULT_LOCALE
        )
        locale = I18nMiddleware.get_preferred_locale(fallback)
        if locale not in LocaleHandler.LOCALE_WHITE_LIST:
            locale = LocaleHandler.DEFAULT_LOCALE
        return locale, False

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
