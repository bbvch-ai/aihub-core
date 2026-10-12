from collections.abc import Iterator
from typing import Annotated, Any, Literal

from dlt.sources.helpers.requests.retry import Client
from dlt.sources.helpers.rest_client import RESTClient
from dlt.sources.helpers.rest_client.auth import BearerTokenAuth, HttpBasicAuth
from requests import Response, Session

from swiss_ai_hub.pipeline.resources.jira.jira_request_error import JiraRequestError

JiraDeployment = Literal["cloud", "data_center"]

_SEARCH_PATHS: dict[str, str] = {"cloud": "rest/api/2/search/jql", "data_center": "rest/api/2/search"}


class JiraClient:
    """Reads issues and comments from Jira Cloud or Data Center over REST v2, which both still serve.

    Stateless and built per run from a database's decrypted configuration. Credentials go into the requests only
    through ``auth``: dlt logs a request's headers at debug level, but never its auth. Every request runs through
    dlt's retrying session, which waits out 429 and 5xx answers.
    """

    PAGE_SIZE = 100

    def __init__(
        self,
        base_url: Annotated[str, "Jira's base URL, including a Data Center context path"],
        deployment: Annotated[JiraDeployment, "Which Jira the URL points at; decides auth and search endpoint"],
        email: Annotated[str, "Account e-mail, Cloud only"],
        token: Annotated[str, "API token (Cloud) or personal access token (Data Center)"],
        session: Annotated[Session | None, "HTTP session; a retrying dlt session when omitted"] = None,
    ):
        self.deployment = deployment
        auth = HttpBasicAuth(username=email, password=token) if deployment == "cloud" else BearerTokenAuth(token=token)
        self._rest = RESTClient(
            base_url=base_url.rstrip("/"), auth=auth, session=session or Client(raise_for_status=False).session
        )

    def search(
        self,
        jql: Annotated[str, "A JQL filter without ORDER BY"],
        fields: Annotated[list[str], "Issue fields to return"],
        rendered: Annotated[bool, "Also return the HTML Jira renders for rich-text fields"] = False,
    ) -> Iterator[list[dict[str, Any]]]:
        """Every issue the JQL matches, a page at a time, in id order.

        Paging ends only when Jira says the result is exhausted, never on a page shorter than asked for: Cloud
        returns fewer issues per page when many fields are requested, and an early stop would make the listing
        partial, which removes files of issues that still exist.
        """
        params = {"fields": ",".join(fields), "maxResults": self.PAGE_SIZE}
        if rendered:
            params["expand"] = "renderedFields"
        if self.deployment == "cloud":
            yield from self._search_cloud(jql, params)
        else:
            yield from self._search_data_center(jql, params)

    def comments(
        self,
        issue_key: Annotated[str, "Key of the issue whose comments to read"],
        with_properties: Annotated[bool, "Also return each comment's properties, where Data Center marks internal"],
    ) -> list[dict[str, Any]]:
        """Every comment of one issue with its rendered HTML, for issues with more comments than a search embeds."""
        expand = "renderedBody,properties" if with_properties else "renderedBody"
        comments: list[dict[str, Any]] = []
        while True:
            page = self._get(
                f"rest/api/2/issue/{issue_key}/comment",
                {"startAt": len(comments), "maxResults": self.PAGE_SIZE, "expand": expand},
            )
            batch = page.get("comments") or []
            comments.extend(batch)
            if not batch or len(comments) >= page.get("total", 0):
                return comments

    def myself(self) -> dict[str, Any]:
        """The account the credentials sign in as; the cheapest call that fails on wrong credentials."""
        return self._get("rest/api/2/myself", {})

    def project(self, key: Annotated[str, "Project key"]) -> dict[str, Any]:
        """Answers 404 for a project that does not exist and for one the account cannot browse alike."""
        return self._get(f"rest/api/2/project/{key}", {})

    def jql_problems(self, jql: Annotated[str, "A JQL query without ORDER BY"]) -> list[str]:
        """What is wrong with a query, checked before it is used.

        Since 2026 Cloud search answers an invalid clause with no issues instead of an error, which would make a
        listing look empty; its parse endpoint still names the problem. Data Center search validates the query and
        answers 400.
        """
        if self.deployment == "cloud":
            answer = self._post("rest/api/3/jql/parse", {"queries": [jql]}, {"validation": "strict"})
            return [error for query in answer.get("queries", []) for error in query.get("errors", [])]
        try:
            self._get(_SEARCH_PATHS["data_center"], {"jql": jql, "maxResults": 0, "startAt": 0})
        except JiraRequestError as refused:
            if refused.status_code != 400:
                raise
            return [refused.jira_messages or str(refused)]
        return []

    def _search_cloud(self, jql: str, params: dict[str, Any]) -> Iterator[list[dict[str, Any]]]:
        """Cloud's search pages by token, with no cap on how far it goes."""
        token: str | None = None
        while True:
            page_params = {**params, "jql": f"{jql} ORDER BY id ASC"}
            if token:
                page_params["nextPageToken"] = token
            page = self._get(_SEARCH_PATHS["cloud"], page_params)
            issues = page.get("issues") or []
            if issues:
                yield issues
            token = page.get("nextPageToken")
            if not issues or page.get("isLast") or not token:
                return

    def _search_data_center(self, jql: str, params: dict[str, Any]) -> Iterator[list[dict[str, Any]]]:
        """Data Center 11 with OpenSearch refuses to page past 10,000 results, so every page is a fresh query for the
        issues after the last id seen (Atlassian's documented workaround)."""
        after: str | None = None
        while True:
            bounded = jql if after is None else f"{jql} AND id > {after}"
            page = self._get(
                _SEARCH_PATHS["data_center"], {**params, "jql": f"{bounded} ORDER BY id ASC", "startAt": 0}
            )
            issues = page.get("issues") or []
            if issues:
                yield issues
            if not issues or len(issues) >= page.get("total", 0):
                return
            after = issues[-1]["id"]

    def _get(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        response = self._rest.get(path, params=params, hooks={"response": [self._raise_for_jira_error]})
        return response.json()

    def _post(self, path: str, body: dict[str, Any], params: dict[str, Any]) -> dict[str, Any]:
        """Only for queries Jira takes as a body; nothing here writes to Jira."""
        response = self._rest.post(path, json=body, params=params, hooks={"response": [self._raise_for_jira_error]})
        return response.json()

    @staticmethod
    def _raise_for_jira_error(response: Response, *args: Any, **kwargs: Any) -> None:
        """A response hook, so the error is raised inside the retrying ``send`` and a 429 is waited out."""
        if not response.ok:
            raise JiraRequestError.from_response(response)
