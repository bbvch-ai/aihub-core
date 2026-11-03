import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from typing import Annotated, Any, ClassVar, Self
from urllib.parse import quote

import httpx

from swiss_ai_hub.core.jira.jira_connection_config import JiraConnectionConfig, JiraDeployment
from swiss_ai_hub.core.jira.jira_error import JiraError
from swiss_ai_hub.core.jira.jira_request_error import JiraRequestError
from swiss_ai_hub.core.jira.jira_too_many_tickets_error import JiraTooManyTicketsError

_SEARCH_PATHS: dict[str, str] = {"cloud": "rest/api/2/search/jql", "data_center": "rest/api/2/search"}


class JiraClient:
    """Reads Jira Cloud or Data Center over REST v2, which both still serve; v3 would return rich text as JSON.

    Opened per read from a connection config and closed after it. The token reaches Jira only through the client's
    auth, never a URL, a log line or an error. Nothing here writes to Jira: the one POST asks Cloud to parse a query.
    Throttling (429) and gateway errors are waited out a few times, never for longer than a chat can wait.
    """

    MAX_ATTEMPTS: ClassVar[int] = 4
    MAX_RETRY_WAIT_SECONDS: ClassVar[float] = 30.0
    FIRST_RETRY_WAIT_SECONDS: ClassVar[float] = 1.0
    RETRIED_STATUSES: ClassVar[frozenset[int]] = frozenset({429, 502, 503, 504})

    def __init__(
        self,
        http: Annotated[httpx.AsyncClient, "Signed-in client whose base URL is Jira's, ending in a slash"],
        deployment: Annotated[JiraDeployment, "Which Jira answers; decides the search endpoint and its paging"],
        page_size: Annotated[int, "Issues asked for per search page"],
    ):
        self._http = http
        self.deployment = deployment
        self._page_size = page_size

    @classmethod
    @asynccontextmanager
    async def connect(
        cls, connection: Annotated[JiraConnectionConfig, "Where Jira is and how to sign in"]
    ) -> AsyncIterator[Self]:
        """Cloud signs in with the account e-mail and an API token, Data Center with a personal access token."""
        cloud = connection.deployment == "cloud"
        async with httpx.AsyncClient(
            base_url=f"{connection.base_url.rstrip('/')}/",
            auth=httpx.BasicAuth(connection.email, connection.api_token) if cloud else None,
            headers={"Accept": "application/json"}
            | ({} if cloud else {"Authorization": f"Bearer {connection.api_token}"}),
            timeout=connection.request_timeout_seconds,
            follow_redirects=False,
        ) as http:
            yield cls(http, connection.deployment, connection.page_size)

    async def search(
        self,
        jql: Annotated[str, "A JQL query without ORDER BY"],
        fields: Annotated[list[str], "Issue fields to return"],
        rendered: Annotated[bool, "Also return the HTML Jira renders for rich-text fields"] = False,
        limit: Annotated[int | None, "Fail rather than return more issues than this"] = None,
    ) -> AsyncIterator[list[dict[str, Any]]]:
        """Every issue the JQL matches, a page at a time.

        Paging ends only when Jira says the result is exhausted, never on a page shorter than asked for: Cloud returns
        fewer issues per page when the fields are large. The query is parenthesised before the order is appended, so
        an ``OR`` in it stays one condition.
        """
        params: dict[str, Any] = {"fields": ",".join(fields), "maxResults": self._page_size}
        if rendered:
            params["expand"] = "renderedFields"
        pages = (
            self._search_cloud(jql, params, limit)
            if self.deployment == "cloud"
            else self._search_data_center(jql, params, limit)
        )
        async for page in pages:
            yield page

    async def myself(self) -> dict[str, Any]:
        """The account the credentials sign in as; the cheapest call that fails on wrong credentials."""
        return await self._get("rest/api/2/myself", {})

    async def project(self, key: Annotated[str, "Project key"]) -> dict[str, Any]:
        """Answers 404 for a project that does not exist and for one the account cannot browse alike."""
        return await self._get(f"rest/api/2/project/{quote(key, safe='')}", {})

    async def project_versions(self, key: Annotated[str, "Project key"]) -> list[dict[str, Any]]:
        """Every version of a project, archived ones included, as Cloud and Data Center both list them."""
        return await self._get_list(f"rest/api/2/project/{quote(key, safe='')}/versions")

    async def jql_problems(self, jql: Annotated[str, "A JQL query without ORDER BY"]) -> list[str]:
        """What is wrong with a query, checked before it is used.

        Cloud search answers an invalid clause with no issues instead of an error, which would look like an empty
        result; its parse endpoint still names the problem. Data Center search validates the query and answers 400.
        """
        if self.deployment == "cloud":
            answer = await self._send(
                "POST", "rest/api/3/jql/parse", params={"validation": "strict"}, json={"queries": [jql]}
            )
            return [error for query in answer.get("queries", []) for error in query.get("errors", [])]
        try:
            await self._get(_SEARCH_PATHS["data_center"], {"jql": jql, "maxResults": 0, "startAt": 0})
        except JiraRequestError as refused:
            if refused.status_code != 400:
                raise
            return [refused.jira_messages or str(refused)]
        return []

    async def _search_cloud(
        self, jql: str, params: dict[str, Any], limit: int | None
    ) -> AsyncIterator[list[dict[str, Any]]]:
        """Cloud's search pages by token and gives no count, so the limit is checked as issues arrive."""
        token: str | None = None
        seen: set[str] = set()
        while True:
            page_params = {**params, "jql": f"({jql}) ORDER BY id ASC"}
            if token:
                page_params["nextPageToken"] = token
            page = await self._get(_SEARCH_PATHS["cloud"], page_params)
            issues = page.get("issues") or []
            self._require_progress(issues, seen)
            if limit is not None and len(seen) > limit:
                raise JiraTooManyTicketsError(limit, None)
            if issues:
                yield issues
            token = page.get("nextPageToken")
            if not issues or page.get("isLast") or not token:
                return

    async def _search_data_center(
        self, jql: str, params: dict[str, Any], limit: int | None
    ) -> AsyncIterator[list[dict[str, Any]]]:
        """Data Center pages by offset, which needs no particular order: its ``ORDER BY id`` sorts by key, so the
        keyset ``id > N`` the pipeline syncs one project with skips issues as soon as a query spans projects.

        Offsets past 10,000 fail on Data Center 11 with OpenSearch, and the limit keeps a read below that. The first
        page counts every match: a search over the limit fails before a second page is fetched, and paging that lost
        issues (one deleted mid-search) fails instead of returning a partial list.
        """
        start = 0
        seen: set[str] = set()
        counted: int | None = None
        while True:
            page = await self._get(
                _SEARCH_PATHS["data_center"], {**params, "jql": f"({jql}) ORDER BY id ASC", "startAt": start}
            )
            if counted is None:
                counted = page.get("total", 0)
                if limit is not None and counted > limit:
                    raise JiraTooManyTicketsError(limit, counted)
            issues = page.get("issues") or []
            self._require_progress(issues, seen)
            if issues:
                yield issues
            start += len(issues)
            if not issues or start >= page.get("total", 0):
                break
        if len(seen) < counted:
            raise JiraError(
                f"Jira counted {counted} issues for the query but paging returned {len(seen)}; the search stops so "
                "that no issue is silently missing."
            )

    @staticmethod
    def _require_progress(issues: list[dict[str, Any]], seen: set[str]) -> None:
        """An issue seen twice means the paging went in a circle, as Cloud's page tokens have been reported to do; it
        would never end."""
        for issue in issues:
            if issue["id"] in seen:
                raise JiraError(f"Jira returned {issue['key']} twice while paging a search; the paging is stuck.")
            seen.add(issue["id"])

    async def _get(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        answer = await self._send("GET", path, params=params)
        if not isinstance(answer, dict):
            raise JiraError(f"Jira answered GET /{path} with a {type(answer).__name__} instead of an object.")
        return answer

    async def _get_list(self, path: str) -> list[dict[str, Any]]:
        """Version lists are JSON arrays, the one kind of answer read here that is not an object."""
        answer = await self._send("GET", path, params={})
        if not isinstance(answer, list):
            raise JiraError(f"Jira answered GET /{path} with a {type(answer).__name__} instead of a list.")
        return answer

    async def _send(self, method: str, path: str, **request: Any) -> Any:
        """Only GETs and Cloud's read-only parse POST pass through here, so a retried request changes nothing."""
        for attempt in range(1, self.MAX_ATTEMPTS + 1):
            response = await self._attempt(method, path, request, last=attempt == self.MAX_ATTEMPTS)
            if response is None:
                await asyncio.sleep(self._backoff(attempt))
                continue
            if response.status_code in self.RETRIED_STATUSES and attempt < self.MAX_ATTEMPTS:
                await asyncio.sleep(self._allowed_wait(response, attempt))
                continue
            if not response.is_success:
                raise JiraRequestError.from_response(response)
            return self._json(response)
        raise AssertionError("unreachable: the last attempt returns or raises")

    async def _attempt(self, method: str, path: str, request: dict[str, Any], last: bool) -> httpx.Response | None:
        """None when the connection was refused and another attempt may follow: the request never reached Jira."""
        try:
            return await self._http.request(method, path, **request)
        except (httpx.ConnectError, httpx.ConnectTimeout) as unreachable:
            if last:
                raise self._unreachable(unreachable) from unreachable
            return None
        except httpx.TransportError as failed:
            raise self._unreachable(failed) from failed

    @classmethod
    def _allowed_wait(cls, response: httpx.Response, attempt: int) -> float:
        """A wait longer than a chat can take fails at once instead of being slept."""
        wait = cls._retry_wait(response, attempt)
        if wait > cls.MAX_RETRY_WAIT_SECONDS:
            raise JiraRequestError.from_response(response, f"Jira asks to wait {wait:.0f} s, so try again later")
        return wait

    def _unreachable(self, failure: httpx.TransportError) -> JiraError:
        """Names the host, never the full URL, whose query string carries the JQL."""
        return JiraError(f"Jira at {self._http.base_url.host} did not respond ({type(failure).__name__}).")

    @classmethod
    def _backoff(cls, attempt: int) -> float:
        return cls.FIRST_RETRY_WAIT_SECONDS * 2 ** (attempt - 1)

    @classmethod
    def _retry_wait(cls, response: httpx.Response, attempt: int) -> float:
        """``Retry-After`` is either seconds or an HTTP date; without it the wait doubles with each attempt."""
        header = response.headers.get("Retry-After", "").strip()
        if not header:
            return cls._backoff(attempt)
        if header.isdigit():
            return float(header)
        try:
            when = parsedate_to_datetime(header)
        except (TypeError, ValueError):
            return cls._backoff(attempt)
        when = when if when.tzinfo else when.replace(tzinfo=UTC)
        return max(0.0, (when - datetime.now(UTC)).total_seconds())

    @staticmethod
    def _json(response: httpx.Response) -> Any:
        """A single sign-on page or a proxy in front of Jira answers 200 with HTML, which is no answer at all."""
        content_type = response.headers.get("Content-Type", "")
        if "json" not in content_type:
            raise JiraError(
                f"The Jira URL answered {response.request.method} {response.request.url.path} with "
                f"{content_type.split(';')[0] or 'no content type'} instead of JSON, so it does not lead to Jira's "
                "REST API; check the URL (a sign-in page or a proxy may be in front of it)."
            )
        return response.json()
