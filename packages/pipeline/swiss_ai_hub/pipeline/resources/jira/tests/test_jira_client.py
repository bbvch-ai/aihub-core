import base64

import pytest

from swiss_ai_hub.pipeline.resources.jira.jira_client import JiraClient
from swiss_ai_hub.pipeline.resources.jira.jira_request_error import JiraRequestError
from swiss_ai_hub.pipeline.resources.jira.tests.fake_jira import FakeJira

_TOKEN = "s3cret-token"


def _jira(monkeypatch: pytest.MonkeyPatch, deployment: str, issues: int = 5, page_size: int = 2) -> FakeJira:
    jira = FakeJira(deployment=deployment, page_size=page_size)
    for number in range(1, issues + 1):
        jira.add_issue(f"AAA-{number}")
    jira.install(monkeypatch)
    return jira


def _client(deployment: str, base_url: str = "https://acme.atlassian.net") -> JiraClient:
    return JiraClient(base_url=base_url, deployment=deployment, email="bot@acme.test", token=_TOKEN)


def _keys(client: JiraClient) -> list[str]:
    return [hit["key"] for page in client.search('project = "AAA"', ["summary"]) for hit in page]


class TestSearch:
    @pytest.mark.parametrize("deployment", ["cloud", "data_center"])
    def test_every_issue_is_returned_in_id_order_across_pages(self, monkeypatch: pytest.MonkeyPatch, deployment: str):
        _jira(monkeypatch, deployment)

        assert _keys(_client(deployment)) == [f"AAA-{number}" for number in range(1, 6)]

    def test_a_page_shorter_than_asked_for_does_not_end_the_search(self, monkeypatch: pytest.MonkeyPatch):
        """Cloud answers 2 issues per page when 100 were asked for; stopping there would make the listing partial."""
        jira = _jira(monkeypatch, "cloud", issues=3, page_size=1)

        assert len(_keys(_client("cloud"))) == 3
        assert len(jira.sent_jql()) == 3

    def test_data_center_pages_by_id_not_by_offset(self, monkeypatch: pytest.MonkeyPatch):
        """Data Center 11 refuses offsets past 10,000, so each page asks for the issues after the last id."""
        jira = _jira(monkeypatch, "data_center", issues=3)

        _keys(_client("data_center"))

        assert jira.sent_jql() == [
            'project = "AAA" ORDER BY id ASC',
            'project = "AAA" AND id > 10002 ORDER BY id ASC',
        ]

    def test_an_empty_project_yields_nothing(self, monkeypatch: pytest.MonkeyPatch):
        _jira(monkeypatch, "cloud", issues=0)

        assert _keys(_client("cloud")) == []

    def test_a_data_center_context_path_is_kept(self, monkeypatch: pytest.MonkeyPatch):
        jira = _jira(monkeypatch, "data_center", issues=1)

        _keys(_client("data_center", base_url="https://acme.atlassian.net/jira/"))

        assert jira.requests[0].url.startswith("https://acme.atlassian.net/jira/rest/api/2/search?")


class TestAuthentication:
    def test_cloud_signs_in_with_the_account_email_and_the_api_token(self, monkeypatch: pytest.MonkeyPatch):
        jira = _jira(monkeypatch, "cloud", issues=1)

        _keys(_client("cloud"))

        expected = base64.b64encode(f"bot@acme.test:{_TOKEN}".encode()).decode()
        assert jira.requests[0].headers["Authorization"] == f"Basic {expected}"

    def test_data_center_signs_in_with_the_personal_access_token(self, monkeypatch: pytest.MonkeyPatch):
        jira = _jira(monkeypatch, "data_center", issues=1)

        _keys(_client("data_center"))

        assert jira.requests[0].headers["Authorization"] == f"Bearer {_TOKEN}"


class TestComments:
    def test_every_comment_is_read_across_pages_with_its_html(self, monkeypatch: pytest.MonkeyPatch):
        jira = FakeJira(page_size=2)
        jira.add_issue("AAA-1", comments=5)
        jira.install(monkeypatch)

        comments = _client("cloud").comments("AAA-1", with_properties=False)

        assert [comment["id"] for comment in comments] == ["1", "2", "3", "4", "5"]
        assert comments[0]["renderedBody"] == "<p>Comment 1</p>"
        assert "expand=renderedBody" in jira.requests[0].url
        assert "properties" not in jira.requests[0].url

    def test_a_page_token_that_keeps_serving_the_first_page_fails_the_search(self, monkeypatch: pytest.MonkeyPatch):
        """Reported for Cloud's /search/jql: fresh tokens, the same first page, and never ``isLast``."""
        jira = _jira(monkeypatch, "cloud")
        jira.stuck_page_tokens = True
        client = _client("cloud")

        with pytest.raises(RuntimeError, match="Jira returned AAA-1 twice while paging"):
            _keys(client)

    def test_data_center_paging_that_skips_an_issue_fails_the_search(self, monkeypatch: pytest.MonkeyPatch):
        """An issue moved into the project keeps its old, lower id; if Jira orders by number, ``id >`` passes it by."""
        jira = FakeJira(deployment="data_center", page_size=2)
        jira.add_issue("AAA-5")
        for number in range(1, 5):
            jira.add_issue(f"AAA-{number}")
        jira.sorted_by_key = True
        jira.install(monkeypatch)
        client = _client("data_center")

        with pytest.raises(RuntimeError, match="Jira counted 5 issues .* but paging returned 4"):
            _keys(client)

    def test_properties_are_asked_for_when_internal_comments_must_be_recognised(self, monkeypatch: pytest.MonkeyPatch):
        jira = FakeJira()
        jira.add_issue("AAA-1", comments=1)
        jira.install(monkeypatch)

        _client("data_center").comments("AAA-1", with_properties=True)

        assert "expand=renderedBody%2Cproperties" in jira.requests[0].url


class TestErrors:
    def test_jira_s_own_reason_names_the_failure(self, monkeypatch: pytest.MonkeyPatch):
        jira = _jira(monkeypatch, "cloud")
        jira.fail_next(400, {"errorMessages": ["Field 'sprnt' does not exist."], "errors": {}})
        client = _client("cloud")

        with pytest.raises(JiraRequestError, match="400 Bad Request to GET /rest/api/2/search/jql: Field 'sprnt'"):
            _keys(client)

    def test_a_missing_reason_phrase_is_filled_in(self, monkeypatch: pytest.MonkeyPatch):
        """Data Center answers ``HTTP/1.1 404`` with no phrase after the code."""
        jira = _jira(monkeypatch, "data_center")
        jira.fail_next(404, {"errorMessages": ["Not found"], "errors": {}})
        client = _client("data_center")

        with pytest.raises(JiraRequestError, match="Jira answered 404 Not Found to GET /rest/api/2/search: Not found"):
            _keys(client)

    def test_rejected_credentials_fail_at_once_without_retrying(self, monkeypatch: pytest.MonkeyPatch):
        jira = _jira(monkeypatch, "cloud")
        jira.fail_next(401, times=5)
        client = _client("cloud")

        with pytest.raises(JiraRequestError, match="401 Unauthorized") as raised:
            _keys(client)

        assert len(jira.requests) == 1
        assert _TOKEN not in str(raised.value)

    def test_a_gateway_error_without_a_body_is_still_retried(self, monkeypatch: pytest.MonkeyPatch):
        jira = _jira(monkeypatch, "cloud", issues=1)
        jira.fail_next(503, b"", times=2)

        assert _keys(_client("cloud")) == ["AAA-1"]
        assert len(jira.requests) == 3

    def test_a_rejection_without_a_body_names_the_status_and_path(self, monkeypatch: pytest.MonkeyPatch):
        jira = _jira(monkeypatch, "cloud")
        jira.fail_next(401, b"")
        client = _client("cloud")

        with pytest.raises(JiraRequestError, match="Jira answered 401 Unauthorized to GET /rest/api/2/search/jql$"):
            _keys(client)

    def test_a_redirect_is_never_followed(self, monkeypatch: pytest.MonkeyPatch):
        """A public address could otherwise send the request on to a host the URL check never saw."""
        jira = _jira(monkeypatch, "cloud")
        jira.fail_next(302, headers={"Location": "http://seaweedfs-filer:8888/buckets/other/x.md"})
        client = _client("cloud")

        with pytest.raises(
            JiraRequestError, match="302 Found to GET /rest/api/2/search/jql; redirects are not followed"
        ):
            _keys(client)

        assert len(jira.requests) == 1

    def test_rate_limiting_is_waited_out(self, monkeypatch: pytest.MonkeyPatch):
        jira = _jira(monkeypatch, "cloud", issues=1)
        jira.fail_next(429, times=2)

        assert _keys(_client("cloud")) == ["AAA-1"]
        assert len(jira.requests) == 3

    def test_the_query_string_never_reaches_the_message(self, monkeypatch: pytest.MonkeyPatch):
        jira = _jira(monkeypatch, "cloud")
        jira.fail_next(400)
        client = _client("cloud")

        with pytest.raises(JiraRequestError) as raised:
            _keys(client)

        assert "?" not in str(raised.value)
        assert "AAA" not in str(raised.value)
