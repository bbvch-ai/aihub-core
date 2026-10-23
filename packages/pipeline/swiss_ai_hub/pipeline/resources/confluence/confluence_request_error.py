from http import HTTPStatus
from typing import Self
from urllib.parse import urlparse

from requests import HTTPError, Response

_STANDARD_REASONS = {status.value: status.phrase for status in HTTPStatus}


class ConfluenceRequestError(HTTPError):
    """A request Confluence answered with an error or a redirect, worded so that a failed sync explains itself on the
    Dagster run page.

    It stays an ``HTTPError`` carrying the response, because that is what dlt's retry inspects: 429 and 5xx are
    retried (honouring ``Retry-After``), everything else fails at once. The message names the status, the path and
    Confluence's own message; it never carries the query string or a credential. A redirect is not followed, because
    the address guard checked the configured host only, so the message names where it leads instead.
    """

    @classmethod
    def from_response(cls, response: Response) -> Self:
        request = f"{response.request.method} {urlparse(response.url).path}"
        reason = response.reason or _STANDARD_REASONS.get(response.status_code, "")
        message = f"Confluence answered {f'{response.status_code} {reason}'.strip()} to {request}"
        if response.is_redirect:
            detail = f"it redirects to {response.headers['Location']}; enter that address as the Confluence URL"
        else:
            detail = cls.confluence_message_of(response)
        return cls(f"{message}: {detail}" if detail else message, response=response)

    @property
    def status_code(self) -> int:
        return self.response.status_code

    @staticmethod
    def confluence_message_of(response: Response) -> str:
        """A gateway in front of Confluence can answer with an empty or garbled JSON body; the status and path still
        say what failed, and the error must stay one dlt retries."""
        if "json" not in response.headers.get("Content-Type", ""):
            return ""
        try:
            body = response.json()
        except ValueError:
            return ""
        return str(body.get("message") or "") if isinstance(body, dict) else ""
