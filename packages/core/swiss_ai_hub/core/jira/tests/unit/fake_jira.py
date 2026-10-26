"""An in-memory Jira answering the REST calls ``JiraClient`` makes, as Jira Cloud or Jira Data Center does.

It is served through ``httpx.MockTransport`` on the very client ``JiraClient.connect`` builds, so retries, auth and
error handling run as in production. Retry waits are recorded instead of slept.
"""

import asyncio
import itertools
import json
import re
import socket
from typing import Any

import httpx
import pytest

PUBLIC_ADDRESS = "93.184.216.34"
_PROJECTS = re.compile(r'project (?:in \(([^)]*)\)|= "([A-Z][A-Z0-9_]*)")')
_FIX_VERSION = re.compile(r'fixVersion = "((?:[^"\\]|\\.)*)"')
_PROJECT_PATH = re.compile(r"/rest/api/2/project/([^/]+)$")

Queued = tuple[int, dict[str, Any] | bytes, dict[str, str]] | type[httpx.TransportError]


class FakeJira:
    """Issues in id order; it pages its answers in ``page_size`` items whatever was asked for, as Jira Cloud does when
    the requested fields are large."""

    def __init__(self, deployment: str = "cloud", site: str = "https://acme.atlassian.net", page_size: int = 2):
        self.deployment = deployment
        self.site = site
        self.page_size = page_size
        self.issues: list[dict[str, Any]] = []
        self.requests: list[httpx.Request] = []
        self.waits: list[float] = []
        self.queued: list[Queued] = []
        self.projects: set[str] = set()
        self.renamed_projects: dict[str, str] = {}
        self.unknown_jql_fields: set[str] = set()
        self.stuck_page_tokens = False
        self.overcount = 0
        self.leaked_issue: dict[str, Any] | None = None
        self.account: dict[str, Any] = {"accountId": "bot-1", "name": "bot", "displayName": "Release Bot"}
        self._ids = itertools.count(10001)

    def install(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Also answers DNS for the host check with a public address, so no test resolves a real name."""
        real_client = httpx.AsyncClient
        real_sleep = asyncio.sleep
        transport = httpx.MockTransport(self.handle)

        async def recorded_sleep(seconds: float) -> None:
            self.waits.append(seconds)
            await real_sleep(0)

        monkeypatch.setattr(
            "swiss_ai_hub.core.jira.jira_client.httpx.AsyncClient",
            lambda **kwargs: real_client(transport=transport, **kwargs),
        )
        monkeypatch.setattr("swiss_ai_hub.core.jira.jira_client.asyncio.sleep", recorded_sleep)
        monkeypatch.setattr(
            "swiss_ai_hub.core.network.source_host_guard.socket.getaddrinfo",
            lambda host, port, **_: [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (PUBLIC_ADDRESS, port))],
        )

    def add_issue(self, key: str, **fields: Any) -> dict[str, Any]:
        issue_id = str(next(self._ids))
        hit = {
            "id": issue_id,
            "key": key,
            "self": f"{self.site}/rest/api/2/issue/{issue_id}",
            "fields": {
                "summary": f"Summary of {key}",
                "issuetype": {"name": "Story"},
                "status": {"name": "To Do"},
                "labels": [],
                "components": [],
                "fixVersions": [],
                "description": f"h2. Raw wiki text of {key}",
                **fields,
            },
            "renderedFields": {"description": f"<h2>Description</h2><p>Rendered text of {key}</p>"},
        }
        self.projects.add(key.rsplit("-", 1)[0])
        self.issues.append(hit)
        return hit

    def fail_next(
        self,
        status: int,
        body: dict[str, Any] | bytes | None = None,
        times: int = 1,
        headers: dict[str, str] | None = None,
    ) -> None:
        """``bytes`` are sent as they are, e.g. HTML from a sign-in page; ``headers`` override the JSON content type."""
        self.queued.extend([(status, {} if body is None else body, headers or {})] * times)

    def raise_next(self, failure: type[httpx.TransportError], times: int = 1) -> None:
        self.queued.extend([failure] * times)

    def sent_jql(self) -> list[str]:
        """The searches made for issues, without the zero-result query Data Center validates a query with."""
        searches = [dict(request.url.params) for request in self.requests if "/search" in request.url.path]
        return [params.get("jql", "") for params in searches if params.get("maxResults") != "0"]

    def handle(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        if self.queued:
            queued = self.queued.pop(0)
            if isinstance(queued, type):
                raise queued("simulated transport failure", request=request)
            return self._response(*queued)
        path = request.url.path
        params = dict(request.url.params)
        if path.endswith("/rest/api/2/myself"):
            return self._response(200, self.account)
        if project := _PROJECT_PATH.search(path):
            return self._project(project.group(1))
        if path.endswith("/rest/api/3/jql/parse") and self.deployment == "cloud":
            return self._response(200, self._parsed(json.loads(request.content)))
        if path.endswith("/rest/api/2/search") and params.get("maxResults") == "0":
            return self._validated(params["jql"])
        if path.endswith("/rest/api/2/search/jql") and self.deployment == "cloud":
            return self._response(200, self._cloud_search(params))
        if path.endswith("/rest/api/2/search") and self.deployment == "data_center":
            return self._response(200, self._data_center_search(params))
        return self._response(404, {"errorMessages": [f"No such endpoint {path} on {self.deployment}"]})

    def _project(self, key: str) -> httpx.Response:
        """Jira answers the same 404 for a missing project and for one the account may not browse."""
        if key in self.projects:
            return self._response(200, {"key": self.renamed_projects.get(key, key), "name": f"Project {key}"})
        return self._response(404, {"errorMessages": [f"No project could be found with key '{key}'."], "errors": {}})

    def _problems(self, jql: str) -> list[str]:
        unknown_fields = [
            f"Field '{field}' does not exist or you do not have permission to view it."
            for field in sorted(self.unknown_jql_fields)
            if field in jql
        ]
        known_versions = {version["name"] for hit in self.issues for version in hit["fields"]["fixVersions"]}
        unknown_versions = [
            f"The value '{version}' does not exist for the field 'fixVersion'."
            for version in (self._unescaped(raw) for raw in _FIX_VERSION.findall(jql))
            if version not in known_versions
        ]
        return unknown_fields + unknown_versions

    def _parsed(self, body: dict[str, Any]) -> dict[str, Any]:
        return {"queries": [{"query": query, "errors": self._problems(query)} for query in body["queries"]]}

    def _validated(self, jql: str) -> httpx.Response:
        problems = self._problems(jql)
        if problems:
            return self._response(400, {"errorMessages": problems, "errors": {}})
        return self._response(200, {"startAt": 0, "maxResults": 0, "total": 0, "issues": []})

    def _cloud_search(self, params: dict[str, str]) -> dict[str, Any]:
        matching = self._matching(params["jql"])
        offset = 0 if self.stuck_page_tokens else int(params.get("nextPageToken", "0"))
        page = matching[offset : offset + self.page_size]
        is_last = offset + self.page_size >= len(matching)
        answer: dict[str, Any] = {"issues": [self._shaped(hit, params) for hit in page], "isLast": is_last}
        if not is_last:
            answer["nextPageToken"] = str(offset + self.page_size)
        return answer

    def _data_center_search(self, params: dict[str, str]) -> dict[str, Any]:
        """Sorted by key whatever ``ORDER BY id`` says, as Data Center 11 does: ENG-50 (id 10134) before SD-1 (id
        10015)."""
        matching = sorted(self._matching(params["jql"]), key=self._key_order)
        start = int(params.get("startAt", "0"))
        return {
            "startAt": start,
            "maxResults": self.page_size,
            "total": len(matching) + self.overcount,
            "issues": [self._shaped(hit, params) for hit in matching[start : start + self.page_size]],
        }

    def _matching(self, jql: str) -> list[dict[str, Any]]:
        """Projects and fix versions, as far as these tests query them, in id order."""
        assert jql.startswith("("), "the client parenthesises the query before appending to it"
        match = _PROJECTS.search(jql)
        listed = match.group(1) or f'"{match.group(2)}"'
        projects = {key.strip().strip('"') for key in listed.split(",")}
        versions = {self._unescaped(raw) for raw in _FIX_VERSION.findall(jql)}
        hits = [
            hit
            for hit in self.issues
            if hit["key"].rsplit("-", 1)[0] in projects
            and (not versions or versions & {version["name"] for version in hit["fields"]["fixVersions"]})
        ]
        if self.leaked_issue:
            hits.append(self.leaked_issue)
        return sorted(hits, key=lambda hit: int(hit["id"]))

    @staticmethod
    def _key_order(hit: dict[str, Any]) -> tuple[str, int]:
        project, number = hit["key"].rsplit("-", 1)
        return project, int(number)

    @staticmethod
    def _shaped(hit: dict[str, Any], params: dict[str, str]) -> dict[str, Any]:
        """Only the requested fields, and the rendered HTML only when asked for."""
        wanted = params.get("fields", "").split(",")
        shaped = {key: value for key, value in hit.items() if key not in ("fields", "renderedFields")}
        shaped["fields"] = {name: value for name, value in hit["fields"].items() if name in wanted}
        if params.get("expand") == "renderedFields":
            shaped["renderedFields"] = {name: value for name, value in hit["renderedFields"].items() if name in wanted}
        return shaped

    @staticmethod
    def _unescaped(literal: str) -> str:
        return re.sub(r"\\(.)", r"\1", literal)

    @staticmethod
    def _response(status: int, body: dict[str, Any] | bytes, headers: dict[str, str] | None = None) -> httpx.Response:
        content = body if isinstance(body, bytes) else json.dumps(body).encode()
        return httpx.Response(status, content=content, headers={"Content-Type": "application/json", **(headers or {})})
