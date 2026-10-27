"""An in-memory Jira answering the REST v2 calls ``JiraClient`` makes, as Jira Cloud or Jira Data Center does.

It is served through a ``requests`` transport adapter mounted on a real dlt retrying session, so the client's retry
and error handling run exactly as in production.
"""

import itertools
import json
import re
import socket
from datetime import datetime
from typing import Any
from urllib.parse import parse_qs, urlparse
from zoneinfo import ZoneInfo

import pytest
from dlt.sources.helpers.requests.retry import Client
from requests import PreparedRequest, Response
from requests.adapters import BaseAdapter

_PROJECT = re.compile(r'project = "([A-Z][A-Z0-9_]*)"')
_AFTER_ID = re.compile(r"AND id > (\d+)")
_COMMENTS = re.compile(r"/rest/api/2/issue/([A-Z0-9_]+-\d+)/comment$")
_PROJECT_PATH = re.compile(r"/rest/api/2/project/([^/]+)$")
_UPDATED_SINCE = re.compile(r'updated >= "(\d{4}/\d{2}/\d{2} \d{2}:\d{2})"')
ZONE = ZoneInfo("Europe/Zurich")


# What every host resolves to in these tests: a public address, so the host check lets it through.
PUBLIC_ADDRESS = "93.184.216.34"


class FakeJiraTransport(BaseAdapter):
    def __init__(self, jira: "FakeJira"):
        super().__init__()
        self.jira = jira

    def send(self, request: PreparedRequest, **kwargs: Any) -> Response:
        self.jira.requests.append(request)
        status, body = self.jira.answer(request)
        response = Response()
        response.status_code = status
        response.reason = {
            200: "OK",
            302: "Found",
            400: "Bad Request",
            401: "Unauthorized",
            429: "Too Many Requests",
        }.get(status, "")
        response.headers["Content-Type"] = "application/json"
        response.headers.update(self.jira.answer_headers)
        response._content = body if isinstance(body, bytes) else json.dumps(body).encode()
        response.url = request.url
        response.request = request
        return response

    def close(self) -> None:
        """Nothing to release: the fake answers from memory and holds no connections."""


class FakeJira:
    """Issues per project and comments per issue; it pages its answers in ``page_size`` items whatever was asked for,
    as Jira Cloud does when many fields are requested."""

    def __init__(self, deployment: str = "cloud", site: str = "https://acme.atlassian.net", page_size: int = 2):
        self.deployment = deployment
        self.site = site
        self.page_size = page_size
        self.issues: dict[str, list[dict[str, Any]]] = {}
        self.paged_comments: dict[str, list[dict[str, Any]]] = {}
        self.requests: list[PreparedRequest] = []
        self.queued_failures: list[tuple[int, dict[str, Any] | bytes, dict[str, str]]] = []
        self.answer_headers: dict[str, str] = {}
        self.projects: set[str] = set()
        self.project_types: dict[str, str] = {}
        self.account: dict[str, Any] = {
            "accountId": "bot-1",
            "name": "bot",
            "displayName": "Seed Bot",
            "timeZone": ZONE.key,
        }
        self.unknown_jql_fields: set[str] = set()
        self.renamed_projects: dict[str, str] = {}
        self.stuck_page_tokens = False
        self.sorted_by_key = False
        self._ids = itertools.count(10001)

    def install(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Also answers DNS for the host check, with a public address, so no test resolves a real name."""
        client = Client(raise_for_status=False, request_backoff_factor=0, request_max_retry_delay=0)
        client.session.mount("https://", FakeJiraTransport(self))
        monkeypatch.setattr("swiss_ai_hub.pipeline.resources.jira.jira_client.Client", lambda **_: client)
        monkeypatch.setattr(
            "swiss_ai_hub.core.network.source_host_guard.socket.getaddrinfo",
            lambda host, port, **_: [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (PUBLIC_ADDRESS, port))],
        )

    def add_issue(self, key: str, *, comments: int = 0, **fields: Any) -> dict[str, Any]:
        project = key.rsplit("-", 1)[0]
        issue_id = str(next(self._ids))
        raw_comments = [self._comment(index) for index in range(1, comments + 1)]
        hit = {
            "id": issue_id,
            "key": key,
            "self": f"{self.site}/rest/api/2/issue/{issue_id}",
            "fields": {
                "summary": f"Summary of {key}",
                "issuetype": {"name": "Story"},
                "status": {"name": "To Do"},
                "priority": {"name": "Medium"},
                "labels": [],
                "components": [],
                "fixVersions": [],
                "reporter": {"displayName": "Rita Reporter", "emailAddress": "rita@acme.test"},
                "assignee": None,
                "created": "2026-10-01T09:00:00.000+0200",
                "updated": "2026-10-02T10:30:00.000+0200",
                "description": "Raw wiki text",
                "comment": {"comments": raw_comments, "total": comments, "maxResults": comments, "startAt": 0},
                **fields,
            },
            "renderedFields": {
                "description": f"<p>Description of {key}</p>",
                "comment": {"comments": [{"id": c["id"], "body": f"<p>Comment {c['id']}</p>"} for c in raw_comments]},
            },
        }
        self.projects.add(project)
        self.issues.setdefault(project, []).append(hit)
        self.paged_comments[key] = [{**c, "renderedBody": f"<p>Comment {c['id']}</p>"} for c in raw_comments]
        return hit

    def fail_next(
        self,
        status: int,
        body: dict[str, Any] | bytes | None = None,
        times: int = 1,
        headers: dict[str, str] | None = None,
    ) -> None:
        """``bytes`` are sent as they are, for a gateway that answers JSON errors without a JSON body; ``headers``
        carry e.g. the ``Location`` of a redirect."""
        self.queued_failures.extend([(status, {} if body is None else body, headers or {})] * times)

    def sent_jql(self) -> list[str]:
        """The searches made for issues, without the zero-result query Data Center validates a clause with."""
        searches = [self._params(request) for request in self.requests if "/search" in request.url]
        return [params.get("jql", "") for params in searches if params.get("maxResults") != "0"]

    def answer(self, request: PreparedRequest) -> tuple[int, dict[str, Any] | bytes]:
        self.answer_headers = {}
        if self.queued_failures:
            status, body, self.answer_headers = self.queued_failures.pop(0)
            return status, body
        path = urlparse(request.url).path
        params = self._params(request)
        if comments := _COMMENTS.search(path):
            return 200, self._comment_page(comments.group(1), params)
        if path.endswith("/rest/api/2/myself"):
            return 200, self.account
        if project := _PROJECT_PATH.search(path):
            return self._project(project.group(1))
        if path.endswith("/rest/api/3/jql/parse") and self.deployment == "cloud":
            return 200, self._parsed(json.loads(request.body))
        if path.endswith("/rest/api/2/search") and params.get("maxResults") == "0":
            return self._validated(params["jql"])
        if path.endswith("/rest/api/2/search/jql") and self.deployment == "cloud":
            return 200, self._cloud_search(params)
        if path.endswith("/rest/api/2/search") and self.deployment == "data_center":
            return 200, self._data_center_search(params)
        return 404, {"errorMessages": [f"No such endpoint {path} on {self.deployment}"]}

    def _project(self, key: str) -> tuple[int, dict[str, Any]]:
        """Jira answers the same 404 for a missing project and for one the account may not browse."""
        if key in self.projects:
            return 200, {
                "key": self.renamed_projects.get(key, key),
                "name": f"Project {key}",
                "projectTypeKey": self.project_types.get(key, "software"),
            }
        return 404, {"errorMessages": [f"No project could be found with key '{key}'."], "errors": {}}

    def _problems(self, jql: str) -> list[str]:
        return [
            f"Field '{field}' does not exist or you do not have permission to view it."
            for field in sorted(self.unknown_jql_fields)
            if field in jql
        ]

    def _parsed(self, body: dict[str, Any]) -> dict[str, Any]:
        return {"queries": [{"query": query, "errors": self._problems(query)} for query in body["queries"]]}

    def _validated(self, jql: str) -> tuple[int, dict[str, Any]]:
        problems = self._problems(jql)
        if problems:
            return 400, {"errorMessages": problems, "errors": {}}
        return 200, {"startAt": 0, "maxResults": 0, "total": 0, "issues": []}

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
        assert params.get("startAt") == "0", "Data Center pages by id, never by offset"
        matching = self._matching(params["jql"])
        page = matching[: self.page_size]
        return {
            "startAt": 0,
            "maxResults": self.page_size,
            "total": len(matching),
            "issues": [self._shaped(h, params) for h in page],
        }

    def _matching(self, jql: str) -> list[dict[str, Any]]:
        """Projects, keyset ids and ``updated >=`` in the account's zone, to the minute, as Jira reads them."""
        project = _PROJECT.search(jql).group(1)
        after = int(match.group(1)) if (match := _AFTER_ID.search(jql)) else -1
        since = None
        if match := _UPDATED_SINCE.search(jql):
            since = datetime.strptime(match.group(1), "%Y/%m/%d %H:%M").replace(tzinfo=ZONE)
        hits = [
            hit
            for hit in self.issues.get(project, [])
            if int(hit["id"]) > after and (since is None or datetime.fromisoformat(hit["fields"]["updated"]) >= since)
        ]
        return sorted(hits, key=self._order)

    def _order(self, hit: dict[str, Any]) -> int:
        """``sorted_by_key`` orders by issue number while ``id >`` still compares ids, the way an issue moved into a
        project keeps its old id under a new, higher number."""
        return int(hit["key"].rsplit("-", 1)[1]) if self.sorted_by_key else int(hit["id"])

    def _shaped(self, hit: dict[str, Any], params: dict[str, str]) -> dict[str, Any]:
        """Only the requested fields, and the rendered HTML only when asked for; Cloud embeds at most 20 comments."""
        wanted = params.get("fields", "").split(",")
        fields = {name: value for name, value in hit["fields"].items() if name in wanted}
        if "comment" in fields:
            embedded = fields["comment"]["comments"][:20]
            fields["comment"] = {**fields["comment"], "comments": embedded, "maxResults": len(embedded)}
        shaped = {key: value for key, value in hit.items() if key not in ("fields", "renderedFields")}
        shaped["fields"] = fields
        if params.get("expand") == "renderedFields":
            rendered = hit["renderedFields"]
            embedded_ids = {c["id"] for c in fields.get("comment", {}).get("comments", [])}
            comments = [c for c in rendered["comment"]["comments"] if c["id"] in embedded_ids]
            shaped["renderedFields"] = {**rendered, "comment": {"comments": comments}}
        return shaped

    def _comment_page(self, key: str, params: dict[str, str]) -> dict[str, Any]:
        """Comment properties come only when asked for, as Jira sends them."""
        everything = self.paged_comments[key]
        if "properties" not in params.get("expand", ""):
            everything = [{k: v for k, v in comment.items() if k != "properties"} for comment in everything]
        start = int(params.get("startAt", "0"))
        page = everything[start : start + self.page_size]
        return {"comments": page, "startAt": start, "maxResults": self.page_size, "total": len(everything)}

    @staticmethod
    def _comment(index: int) -> dict[str, Any]:
        return {
            "id": str(index),
            "author": {"displayName": f"Commenter {index}"},
            "body": f"Raw comment {index}",
            "created": f"2026-10-03T{8 + index % 10:02d}:00:00.000+0200",
        }

    @staticmethod
    def _params(request: PreparedRequest) -> dict[str, str]:
        return {name: values[0] for name, values in parse_qs(urlparse(request.url).query).items()}
