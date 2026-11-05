from enum import StrEnum


class WebFetchFailureReason(StrEnum):
    """Why a linked page could not be read, so the answer can tell the user instead of inventing the page."""

    MALFORMED_URL = "malformed_url"
    UNSUPPORTED_URL = "unsupported_url"
    BLOCKED_HOST = "blocked_host"
    NOT_FOUND = "not_found"
    ACCESS_DENIED = "access_denied"
    HTTP_ERROR = "http_error"
    TIMEOUT = "timeout"
    UNSUPPORTED_CONTENT = "unsupported_content"
    EMPTY_CONTENT = "empty_content"
    URL_LIMIT_REACHED = "url_limit_reached"
