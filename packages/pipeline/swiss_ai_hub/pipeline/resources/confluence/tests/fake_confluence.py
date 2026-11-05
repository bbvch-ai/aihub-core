"""An in-memory Confluence answering the REST v1 calls ``ConfluenceClient`` makes, as Confluence Cloud or Data Center.

It is served through a ``requests`` transport adapter mounted on a real dlt retrying session, so the client's retry
and error handling run exactly as in production. Search results come a few at a time with a ``_links.next`` relative
to the site, as Confluence returns them: a client that joins it onto the host instead loses Cloud's ``/wiki``.
"""

import json
import re
from typing import Any
from urllib.parse import parse_qs, unquote, urlencode, urlparse

import pytest
from dlt.sources.helpers.requests.retry import Client
from requests import PreparedRequest, Response
from requests.adapters import BaseAdapter

SITES = {"cloud": "https://acme.atlassian.net/wiki", "data_center": "https://confluence.acme.ch"}
_ID_LIST = re.compile(r"^id in \(([0-9, ]+)\)$")
_ONE_ID = re.compile(r"^id = (\d+)$")
_SPACE_QUERY = re.compile(r'^type = space and space = "((?:[^"\\]|\\.)*)"$')
# Properties a search result carries only when asked to expand them, by the key they appear under.
_EXPANDABLE = {"body.storage": "body", "metadata.labels": "metadata"}
_REASONS = {
    200: "OK",
    302: "Found",
    400: "Bad Request",
    401: "Unauthorized",
    404: "Not Found",
    429: "Too Many Requests",
}

type Answer = tuple[int, dict[str, Any] | bytes, dict[str, str]]


class FakeConfluenceTransport(BaseAdapter):
    def __init__(self, confluence: "FakeConfluence"):
        super().__init__()
        self.confluence = confluence

    def send(self, request: PreparedRequest, *args: Any, **kwargs: Any) -> Response:
        self.confluence.requests.append(request)
        status, body, headers = self.confluence.answer(request)
        response = Response()
        response.status_code = status
        response.reason = _REASONS.get(status, "")
        response.headers.update({"Content-Type": "application/json", **headers})
        response._content = body if isinstance(body, bytes) else json.dumps(body).encode()
        response.url = request.url or ""
        response.request = request
        return response

    def close(self) -> None:
        """Nothing to release: the fake answers from memory and holds no connections."""


class FakeConfluence:
    """One site's spaces and pages. Search answers come ``page_size`` results at a time whatever was asked for; only an
    ID list is interpreted, and any other query stands for the configured scope and matches every page."""

    def __init__(self, deployment: str = "cloud", page_size: int = 2):
        self.deployment = deployment
        self.site = SITES[deployment]
        self.page_size = page_size
        self.account: dict[str, Any] = {"type": "known", "accountId": "5d1a", "displayName": "Sync Bot"}
        self.spaces: set[str] = set()
        self.pages: list[dict[str, Any]] = []
        self.requests: list[PreparedRequest] = []
        self.queued_failures: list[Answer] = []
        self.next_link_prefix = ""

    def install(self, monkeypatch: pytest.MonkeyPatch) -> None:
        client = Client(raise_for_status=False, request_backoff_factor=0, request_max_retry_delay=0)
        client.session.mount("https://", FakeConfluenceTransport(self))
        monkeypatch.setattr("swiss_ai_hub.pipeline.resources.confluence.confluence_client.Client", lambda **_: client)

    def add_page(
        self,
        page_id: str,
        title: str,
        *,
        space: str = "ENG",
        ancestors: list[tuple[str, str]] | None = None,
        status: str = "current",
        body: str = "<p>Body</p>",
        version: int = 1,
        labels: list[str] | None = None,
    ) -> dict[str, Any]:
        """A page as REST v1 returns it with every expansion the sync asks for."""
        page = {
            "id": page_id,
            "type": "page",
            "status": status,
            "title": title,
            "space": {"key": space, "name": f"{space} space"},
            "ancestors": [{"id": ancestor_id, "title": ancestor} for ancestor_id, ancestor in ancestors or []],
            "version": {"number": version, "when": "2026-10-01T09:00:00.000Z", "by": {"displayName": "Ada Lovelace"}},
            "history": {"createdDate": "2026-09-01T08:00:00.000Z", "createdBy": {"displayName": "Ada Lovelace"}},
            "metadata": {"labels": {"results": [{"name": label} for label in labels or []]}},
            "body": {"storage": {"value": body, "representation": "storage"}},
            "_links": {"webui": f"/spaces/{space}/pages/{page_id}", "self": f"{self.site}/rest/api/content/{page_id}"},
        }
        self.pages.append(page)
        self.spaces.add(space)
        return page

    def page(self, page_id: str) -> dict[str, Any]:
        return next(page for page in self.pages if page["id"] == page_id)

    def edit(self, page_id: str, body: str) -> None:
        page = self.page(page_id)
        page["body"]["storage"]["value"] = body
        page["version"]["number"] += 1

    def rename(self, page_id: str, title: str) -> None:
        """The renamed page gets a new version; its descendants' ancestor lists change, but their versions do not."""
        self.page(page_id).update(title=title)
        self.page(page_id)["version"]["number"] += 1
        for page in self.pages:
            for ancestor in page["ancestors"]:
                if ancestor["id"] == page_id:
                    ancestor["title"] = title

    def move(self, page_id: str, parent_id: str) -> None:
        """Moving a page changes no version at all, its own or its descendants'; only their ancestor lists change."""
        parent = self.page(parent_id)
        new_chain = [*parent["ancestors"], {"id": parent["id"], "title": parent["title"]}]
        old_depth = len(self.page(page_id)["ancestors"])
        for page in self.pages:
            ids = [ancestor["id"] for ancestor in page["ancestors"]]
            if page["id"] == page_id:
                page["ancestors"] = list(new_chain)
            elif page_id in ids:
                page["ancestors"] = [*new_chain, *page["ancestors"][old_depth:]]

    def relabel(self, page_id: str, labels: list[str]) -> None:
        """Labels are not part of a page's content, so changing them gives the page no new version."""
        self.page(page_id)["metadata"]["labels"]["results"] = [{"name": label} for label in labels]

    def remove(self, page_id: str) -> None:
        self.pages = [page for page in self.pages if page["id"] != page_id]

    def fail_next(
        self,
        status: int,
        body: dict[str, Any] | bytes | None = None,
        times: int = 1,
        headers: dict[str, str] | None = None,
    ) -> None:
        """``bytes`` are sent as they are, for a gateway that answers JSON errors without a JSON body."""
        self.queued_failures.extend([(status, {} if body is None else body, headers or {})] * times)

    def searches(self) -> list[dict[str, str]]:
        """The query parameters of every search the client sent, in order."""
        return [self._params(request) for request in self.requests if self._path(request).endswith("/content/search")]

    def answer(self, request: PreparedRequest) -> Answer:
        if self.queued_failures:
            return self.queued_failures.pop(0)
        api = f"{urlparse(self.site).path}/rest/api/"
        path = self._path(request)
        if not path.startswith(api):
            return 404, {"message": f"No such endpoint {path}"}, {}
        resource = unquote(path.removeprefix(api))
        if resource == "user/current":
            return 200, self.account, {}
        if resource == "search":
            return 200, self._space_search(self._params(request)["cql"]), {}
        if resource == "content/search":
            return 200, self._search(self._params(request)), {}
        # Cloud's REST v1 no longer serves space/{key} or content/{id}; a call to either gets Cloud's 404.
        return 404, {"message": f"No such endpoint {path}"}, {}

    def _space_search(self, cql: str) -> dict[str, Any]:
        """A space the account cannot see is not found, exactly like one that does not exist."""
        match = _SPACE_QUERY.match(cql)
        key = match.group(1).replace('\\"', '"').replace("\\\\", "\\") if match else None
        results = [{"entityType": "space", "space": {"key": key, "name": f"{key} space"}}] if key in self.spaces else []
        return {"results": results, "size": len(results)}

    def _search(self, params: dict[str, str]) -> dict[str, Any]:
        expanded = params.get("expand", "").split(",")
        hidden = {key for expansion, key in _EXPANDABLE.items() if expansion not in expanded}
        matched = [
            {key: value for key, value in page.items() if key not in hidden} for page in self._matching(params["cql"])
        ]
        start = int(params.get("cursor", 0))
        answer: dict[str, Any] = {"results": matched[start : start + self.page_size], "_links": {"base": self.site}}
        if start + self.page_size < len(matched):
            query = urlencode({**params, "cursor": start + self.page_size})
            answer["_links"]["next"] = f"{self.next_link_prefix}/rest/api/content/search?{query}"
        return answer

    def _matching(self, cql: str) -> list[dict[str, Any]]:
        if match := _ID_LIST.match(cql) or _ONE_ID.match(cql):
            wanted = {page_id.strip() for page_id in match.group(1).split(",")}
            return [page for page in self.pages if page["id"] in wanted]
        return list(self.pages)

    @staticmethod
    def _path(request: PreparedRequest) -> str:
        return urlparse(request.url or "").path

    @staticmethod
    def _params(request: PreparedRequest) -> dict[str, str]:
        return {key: values[0] for key, values in parse_qs(urlparse(request.url or "").query).items()}
