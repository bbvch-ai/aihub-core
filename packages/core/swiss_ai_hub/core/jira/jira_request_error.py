from http import HTTPStatus
from typing import Annotated, Self

import httpx

from swiss_ai_hub.core.jira.jira_error import JiraError

_STANDARD_REASONS = {status.value: status.phrase for status in HTTPStatus}


class JiraRequestError(JiraError):
    """A request Jira answered with an error status.

    The message names the status, the path and Jira's own error messages. It keeps neither the httpx request nor the
    response, whose representations carry the query string. Data Center sends no reason phrase, so the standard one
    stands in for it.
    """

    def __init__(
        self,
        message: Annotated[str, "What failed, without the query string or a credential"],
        status_code: Annotated[int, "The HTTP status Jira answered with"],
        path: Annotated[str, "The request path, including a Data Center context path"],
        jira_messages: Annotated[str, "Jira's own words for the error; empty when it gave none"],
    ):
        super().__init__(message)
        self.status_code = status_code
        self.path = path
        self.jira_messages = jira_messages

    @classmethod
    def from_response(
        cls,
        response: Annotated[httpx.Response, "Jira's answer"],
        note: Annotated[str | None, "Why the answer was not waited out or followed"] = None,
    ) -> Self:
        path = response.request.url.path
        reason = response.reason_phrase or _STANDARD_REASONS.get(response.status_code, "")
        message = f"Jira answered {f'{response.status_code} {reason}'.strip()} to {response.request.method} {path}"
        if response.is_redirect:
            note = "redirects are not followed, so enter the address Jira answers at"
        detail = cls.jira_messages_of(response)
        if detail:
            message = f"{message}: {detail}"
        if note:
            message = f"{message}; {note}"
        return cls(message, response.status_code, path, detail)

    @staticmethod
    def jira_messages_of(response: Annotated[httpx.Response, "Jira's answer"]) -> str:
        """A gateway in front of Jira can answer with an empty or garbled JSON body; the status and path still say
        what failed."""
        if "json" not in response.headers.get("Content-Type", ""):
            return ""
        try:
            body = response.json()
        except ValueError:
            return ""
        if not isinstance(body, dict):
            return ""
        field_errors = [f"{field}: {error}" for field, error in (body.get("errors") or {}).items()]
        return "; ".join([*body.get("errorMessages", []), *field_errors])
