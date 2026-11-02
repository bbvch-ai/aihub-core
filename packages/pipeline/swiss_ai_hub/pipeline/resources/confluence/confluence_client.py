from collections.abc import Iterator
from typing import Annotated, Any, Literal

from dlt.sources.helpers.requests.retry import Client
from dlt.sources.helpers.rest_client import RESTClient
from dlt.sources.helpers.rest_client.auth import BearerTokenAuth, HttpBasicAuth
from requests import Response, Session

from swiss_ai_hub.pipeline.resources.confluence.confluence_next_link_paginator import ConfluenceNextLinkPaginator
from swiss_ai_hub.pipeline.resources.confluence.confluence_request_error import ConfluenceRequestError

ConfluenceDeployment = Literal["cloud", "data_center"]


class ConfluenceClient:
    """Reads pages from Confluence Cloud or Data Center over REST v1, the only API both serve: v2 has no CQL search
    and does not exist on Data Center.

    Stateless and built per run from a database's decrypted configuration. Credentials go into the requests only
    through ``auth``: dlt logs a request's headers at debug level, but never its auth. Every request runs through
    dlt's retrying session, which waits out 429 and 5xx answers, and none follows a redirect.
    """

    PAGE_SIZE = 50
    IDS_PER_QUERY = 25

    def __init__(
        self,
        base_url: Annotated[str, "Confluence's base URL: …/wiki on Cloud, including a Data Center context path"],
        deployment: Annotated[ConfluenceDeployment, "Which Confluence the URL points at; decides auth"],
        email: Annotated[str, "Account e-mail, Cloud only"],
        token: Annotated[str, "API token (Cloud) or personal access token (Data Center)"],
        session: Annotated[Session | None, "HTTP session; a retrying dlt session when omitted"] = None,
    ):
        site_url = base_url.rstrip("/")
        auth = HttpBasicAuth(username=email, password=token) if deployment == "cloud" else BearerTokenAuth(token=token)
        self._rest = RESTClient(
            base_url=f"{site_url}/rest/api",
            auth=auth,
            paginator=ConfluenceNextLinkPaginator(site_url),
            data_selector="results",
            session=session or Client(raise_for_status=False).session,
        )

    def search(
        self,
        cql: Annotated[str, "A CQL query"],
        expand: Annotated[str, "Properties to expand on each result, comma-separated"],
    ) -> Iterator[list[dict[str, Any]]]:
        """Every page the query matches, a page of results at a time, until Confluence gives no next link.

        Paging never stops on a page shorter than asked for: Confluence returns fewer results when expansions are
        heavy, and an early stop would make the listing partial, which removes files of pages that still exist.
        """
        for results in self._rest.paginate(
            "content/search",
            params={"cql": cql, "expand": expand, "limit": self.PAGE_SIZE},
            hooks={"response": [self._raise_for_confluence_error]},
            allow_redirects=False,
        ):
            yield list(results)

    def pages_by_id(
        self,
        page_ids: Annotated[list[str], "IDs of the pages to read, as Confluence returned them"],
        expand: Annotated[str, "Properties to expand on each page, comma-separated"],
    ) -> Iterator[list[dict[str, Any]]]:
        """The given pages, one query per batch of IDs, so a long list never outgrows the query string."""
        for start in range(0, len(page_ids), self.IDS_PER_QUERY):
            yield from self.search(f"id in ({', '.join(page_ids[start : start + self.IDS_PER_QUERY])})", expand)

    def current_user(self) -> dict[str, Any]:
        """The account the credentials sign in as; the cheapest call that fails on wrong credentials."""
        return self._get("user/current", {})

    def find_space(self, key: Annotated[str, "Space key"]) -> dict[str, Any] | None:
        """The space, or None when it does not exist or the account cannot see it.

        Looked up through CQL search, because Confluence Cloud's REST v1 no longer serves a space by its key (v2 does,
        but Data Center has no v2). Search answers the same on both editions, under the scope every sync already
        needs.
        """
        answer = self._get("search", {"cql": f"type = space and space = {self.cql_string(key)}", "limit": 1})
        return next(iter(answer.get("results") or []), None)

    def find_page(self, page_id: Annotated[str, "Page ID, digits only"]) -> dict[str, Any] | None:
        """The page with its space, without its body, or None when it does not exist or the account cannot see it.
        Searched for the same reason as a space: Cloud's REST v1 no longer serves a page by its ID."""
        answer = self._get("content/search", {"cql": f"id = {page_id}", "expand": "space", "limit": 1})
        return next(iter(answer.get("results") or []), None)

    @staticmethod
    def cql_string(value: str) -> str:
        """A value as a CQL string literal. Whoever configures a database writes these values, so a quote or a
        backslash in one stays inside the literal instead of changing the query."""
        return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'

    def _get(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        response = self._rest.get(
            path, params=params, hooks={"response": [self._raise_for_confluence_error]}, allow_redirects=False
        )
        return response.json()

    @staticmethod
    def _raise_for_confluence_error(response: Response, *args: Any, **kwargs: Any) -> None:
        """A response hook, so the error is raised inside the retrying ``send`` and a 429 is waited out."""
        if response.is_redirect or not response.ok:
            raise ConfluenceRequestError.from_response(response)
