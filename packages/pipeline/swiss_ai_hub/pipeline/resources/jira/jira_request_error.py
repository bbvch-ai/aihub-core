from typing import Self
from urllib.parse import urlparse

from requests import HTTPError, Response


class JiraRequestError(HTTPError):
    """A request Jira answered with an error, worded so that a failed sync explains itself on the Dagster run page.

    It stays an ``HTTPError`` carrying the response, because that is what dlt's retry inspects: 429 and 5xx are
    retried (honouring ``Retry-After``), everything else fails at once. The message names the status, the path and
    Jira's own error messages; it never carries the query string or a credential.
    """

    @classmethod
    def from_response(cls, response: Response) -> Self:
        request = f"{response.request.method} {urlparse(response.url).path}"
        message = f"Jira answered {response.status_code} {response.reason} to {request}"
        detail = cls.jira_messages_of(response)
        return cls(f"{message}: {detail}" if detail else message, response=response)

    @property
    def status_code(self) -> int:
        return self.response.status_code

    @property
    def jira_messages(self) -> str:
        """Jira's own words for the error, without the status and path around them."""
        return self.jira_messages_of(self.response)

    @staticmethod
    def jira_messages_of(response: Response) -> str:
        if "json" not in response.headers.get("Content-Type", ""):
            return ""
        body = response.json()
        if not isinstance(body, dict):
            return ""
        field_errors = [f"{field}: {error}" for field, error in (body.get("errors") or {}).items()]
        return "; ".join([*body.get("errorMessages", []), *field_errors])
