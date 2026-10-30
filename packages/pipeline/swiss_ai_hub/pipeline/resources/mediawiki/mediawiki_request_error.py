from http import HTTPStatus
from typing import Any, Self
from urllib.parse import urlparse

from requests import HTTPError, Response

_STANDARD_REASONS = {status.value: status.phrase for status in HTTPStatus}


class MediaWikiRequestError(HTTPError):
    """A request MediaWiki answered with an error or a redirect, worded so that a failed sync explains itself on the
    Dagster run page.

    MediaWiki reports most API errors with status 200 and an ``error`` object, so ``code`` carries MediaWiki's own
    error code (``readapidenied``, ``nosuchpageid``) when there is one. It stays an ``HTTPError`` carrying the response,
    because that is what dlt's retry inspects: 429 and 5xx are retried, everything else fails at once. The message
    names the status, the path and MediaWiki's message; never the query string, which can carry a token.
    """

    def __init__(self, message: str, *, response: Response, code: str | None = None):
        super().__init__(message, response=response)
        self.code = code

    @classmethod
    def from_response(cls, response: Response) -> Self:
        request = f"{response.request.method} {urlparse(response.url).path}"
        reason = response.reason or _STANDARD_REASONS.get(response.status_code, "")
        message = f"MediaWiki answered {f'{response.status_code} {reason}'.strip()} to {request}"
        if response.is_redirect:
            detail = f"it redirects to {response.headers['Location']}; enter that address as the wiki URL"
            return cls(f"{message}: {detail}", response=response)
        error = cls.api_error_of(response) or {}
        detail = str(error.get("info") or cls._gateway_reason_of(response)).strip()
        code = str(error["code"]) if error.get("code") else None
        return cls(f"{message}: {detail}" if detail else message, response=response, code=code)

    @classmethod
    def from_api_error(cls, response: Response, error: dict[str, Any]) -> Self:
        code = str(error.get("code") or "unknown")
        info = str(error.get("info") or "").strip()
        action = f"{response.request.method} {urlparse(response.url).path}"
        return cls(f"MediaWiki refused {action} ({code}){f': {info}' if info else ''}", response=response, code=code)

    @property
    def status_code(self) -> int:
        return self.response.status_code

    @staticmethod
    def _gateway_reason_of(response: Response) -> str:
        """Why a gateway in front of the wiki refused a request; Wikimedia's answers a refused OAuth token with
        ``{"httpCode": 401, "httpReason": …}`` instead of a MediaWiki error."""
        if "json" not in response.headers.get("Content-Type", ""):
            return ""
        try:
            body = response.json()
        except ValueError:
            return ""
        return str(body.get("httpReason") or "") if isinstance(body, dict) else ""

    @staticmethod
    def api_error_of(response: Response) -> dict[str, Any] | None:
        """The ``error`` object of a JSON answer, or None. A gateway in front of the wiki can answer with HTML or a
        garbled body; that is no API error, and the caller's own checks decide what it means."""
        if "json" not in response.headers.get("Content-Type", ""):
            return None
        try:
            body = response.json()
        except ValueError:
            return None
        error = body.get("error") if isinstance(body, dict) else None
        return error if isinstance(error, dict) else None
