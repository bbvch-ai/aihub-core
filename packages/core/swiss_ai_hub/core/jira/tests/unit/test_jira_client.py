import base64
from datetime import UTC, datetime, timedelta
from email.utils import format_datetime

import httpx
import pytest

from swiss_ai_hub.core.jira.jira_client import JiraClient
from swiss_ai_hub.core.jira.jira_connection_config import JiraConnectionConfig
from swiss_ai_hub.core.jira.jira_error import JiraError
from swiss_ai_hub.core.jira.jira_request_error import JiraRequestError
from swiss_ai_hub.core.jira.jira_too_many_tickets_error import JiraTooManyTicketsError
from swiss_ai_hub.core.jira.tests.unit.fake_jira import FakeJira

_TOKEN = "s3cret-token"
_SCOPE = 'project in ("AAA")'


def _jira(monkeypatch: pytest.MonkeyPatch, deployment: str, issues: int = 5, page_size: int = 2) -> FakeJira:
    jira = FakeJira(deployment=deployment, page_size=page_size)
    for number in range(1, issues + 1):
        jira.add_issue(f"AAA-{number}")
    jira.install(monkeypatch)
    return jira


def _connection(deployment: str, base_url: str = "https://acme.atlassian.net") -> JiraConnectionConfig:
    return JiraConnectionConfig(base_url=base_url, deployment=deployment, email="bot@acme.test", api_token=_TOKEN)


async def _keys(deployment: str, jql: str = _SCOPE, limit: int | None = None, **connection: str) -> list[str]:
    async with JiraClient.connect(_connection(deployment, **connection)) as client:
        return [hit["key"] async for page in client.search(jql, ["summary"], limit=limit) for hit in page]


async def _project(key: str) -> dict:
    async with JiraClient.connect(_connection("cloud")) as client:
        return await client.project(key)


async def _jql_problems(deployment: str, jql: str) -> list[str]:
    async with JiraClient.connect(_connection(deployment)) as client:
        return await client.jql_problems(jql)


async def _myself(deployment: str = "cloud") -> dict:
    async with JiraClient.connect(_connection(deployment)) as client:
        return await client.myself()


class TestSearch:
    @pytest.mark.asyncio
    @pytest.mark.parametrize("deployment", ["cloud", "data_center"])
    async def test_every_issue_is_returned_in_id_order_across_pages(
        self, monkeypatch: pytest.MonkeyPatch, deployment: str
    ):
        _jira(monkeypatch, deployment)

        assert await _keys(deployment) == [f"AAA-{number}" for number in range(1, 6)]

    @pytest.mark.asyncio
    async def test_a_page_shorter_than_asked_for_does_not_end_the_search(self, monkeypatch: pytest.MonkeyPatch):
        """Cloud answers fewer issues than the 100 asked for when fields are large; stopping there loses issues."""
        jira = _jira(monkeypatch, "cloud", issues=3, page_size=1)

        assert len(await _keys("cloud")) == 3
        assert len(jira.sent_jql()) == 3

    @pytest.mark.asyncio
    async def test_data_center_pages_by_offset_with_the_query_in_parentheses(self, monkeypatch: pytest.MonkeyPatch):
        jira = _jira(monkeypatch, "data_center", issues=3)
        query = 'project in ("AAA") OR labels = "x"'

        await _keys("data_center", jql=query)

        searches = [dict(request.url.params) for request in jira.requests]
        assert [(params["jql"], params["startAt"]) for params in searches] == [
            (f"({query}) ORDER BY id ASC", "0"),
            (f"({query}) ORDER BY id ASC", "2"),
        ]

    @pytest.mark.asyncio
    async def test_data_center_returns_every_issue_of_several_projects(self, monkeypatch: pytest.MonkeyPatch):
        """Data Center sorts ``ORDER BY id`` by key, so BBB-1 (an old id) comes after AAA-3 (a newer one): paging
        by ``id > last`` would skip it, found live with ENG + SD on Data Center 11.3."""
        jira = FakeJira(deployment="data_center", page_size=2)
        jira.add_issue("AAA-1")
        jira.add_issue("BBB-1")
        jira.add_issue("AAA-2")
        jira.add_issue("AAA-3")
        jira.install(monkeypatch)

        keys = await _keys("data_center", jql='project in ("AAA","BBB")')

        assert sorted(keys) == ["AAA-1", "AAA-2", "AAA-3", "BBB-1"]

    @pytest.mark.asyncio
    async def test_cloud_sends_the_query_in_parentheses_before_its_order(self, monkeypatch: pytest.MonkeyPatch):
        jira = _jira(monkeypatch, "cloud", issues=1)

        await _keys("cloud")

        assert jira.sent_jql() == [f"({_SCOPE}) ORDER BY id ASC"]

    @pytest.mark.asyncio
    @pytest.mark.parametrize("deployment", ["cloud", "data_center"])
    async def test_nothing_matching_yields_nothing(self, monkeypatch: pytest.MonkeyPatch, deployment: str):
        _jira(monkeypatch, deployment, issues=0)

        assert await _keys(deployment) == []

    @pytest.mark.asyncio
    async def test_a_data_center_context_path_is_kept(self, monkeypatch: pytest.MonkeyPatch):
        jira = _jira(monkeypatch, "data_center", issues=1)

        await _keys("data_center", base_url="https://jira.acme.ch/jira/")

        assert str(jira.requests[0].url).startswith("https://jira.acme.ch/jira/rest/api/2/search?")

    @pytest.mark.asyncio
    async def test_a_page_token_that_loops_fails_the_search(self, monkeypatch: pytest.MonkeyPatch):
        jira = _jira(monkeypatch, "cloud", issues=3)
        jira.stuck_page_tokens = True

        with pytest.raises(JiraError, match="returned AAA-1 twice while paging"):
            await _keys("cloud")

    @pytest.mark.asyncio
    async def test_data_center_returning_fewer_issues_than_it_counted_fails(self, monkeypatch: pytest.MonkeyPatch):
        jira = _jira(monkeypatch, "data_center", issues=3)
        jira.overcount = 1

        with pytest.raises(JiraError, match="counted 4 issues for the query but paging returned 3"):
            await _keys("data_center")


class TestLimit:
    @pytest.mark.asyncio
    async def test_data_center_refuses_before_the_second_page(self, monkeypatch: pytest.MonkeyPatch):
        """Data Center counts the matches on the first page, so nothing beyond it is fetched."""
        jira = _jira(monkeypatch, "data_center", issues=5)

        with pytest.raises(JiraTooManyTicketsError, match="matches 5 tickets, more than the 4 read at once") as refused:
            await _keys("data_center", limit=4)

        assert (refused.value.limit, refused.value.counted) == (4, 5)
        assert len(jira.sent_jql()) == 1

    @pytest.mark.asyncio
    async def test_cloud_refuses_once_more_issues_than_allowed_arrived(self, monkeypatch: pytest.MonkeyPatch):
        _jira(monkeypatch, "cloud", issues=5)

        with pytest.raises(JiraTooManyTicketsError, match="matches more than the 3 tickets read at once") as refused:
            await _keys("cloud", limit=3)

        assert refused.value.counted is None

    @pytest.mark.asyncio
    @pytest.mark.parametrize("deployment", ["cloud", "data_center"])
    async def test_exactly_the_limit_is_returned(self, monkeypatch: pytest.MonkeyPatch, deployment: str):
        _jira(monkeypatch, deployment, issues=4)

        assert len(await _keys(deployment, limit=4)) == 4


class TestAuthentication:
    @pytest.mark.asyncio
    async def test_cloud_signs_in_with_the_account_email_and_the_api_token(self, monkeypatch: pytest.MonkeyPatch):
        jira = _jira(monkeypatch, "cloud", issues=1)

        await _keys("cloud")

        expected = base64.b64encode(f"bot@acme.test:{_TOKEN}".encode()).decode()
        assert jira.requests[0].headers["Authorization"] == f"Basic {expected}"

    @pytest.mark.asyncio
    async def test_data_center_signs_in_with_the_personal_access_token(self, monkeypatch: pytest.MonkeyPatch):
        jira = _jira(monkeypatch, "data_center", issues=1)

        await _keys("data_center")

        assert jira.requests[0].headers["Authorization"] == f"Bearer {_TOKEN}"

    @pytest.mark.asyncio
    async def test_the_token_is_never_part_of_a_url(self, monkeypatch: pytest.MonkeyPatch):
        jira = _jira(monkeypatch, "data_center", issues=3)

        await _keys("data_center")

        assert not any(_TOKEN in str(request.url) for request in jira.requests)


class TestErrors:
    @pytest.mark.asyncio
    async def test_a_refused_sign_in_names_status_path_and_jira_message_but_not_the_token(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        jira = _jira(monkeypatch, "cloud", issues=0)
        jira.fail_next(401, {"errorMessages": ["You are not authenticated."]})

        with pytest.raises(JiraRequestError) as refused:
            await _myself()

        assert str(refused.value) == (
            "Jira answered 401 Unauthorized to GET /rest/api/2/myself: You are not authenticated."
        )
        assert (refused.value.status_code, refused.value.path) == (401, "/rest/api/2/myself")
        assert _TOKEN not in str(refused.value)

    @pytest.mark.asyncio
    async def test_the_query_string_stays_out_of_the_message(self, monkeypatch: pytest.MonkeyPatch):
        jira = _jira(monkeypatch, "data_center", issues=0)
        jira.fail_next(400, {"errorMessages": ["Bad"]})

        with pytest.raises(JiraRequestError) as refused:
            await _keys("data_center", jql='project in ("SECRETPROJECT")')

        assert "SECRETPROJECT" not in str(refused.value)

    @pytest.mark.asyncio
    async def test_a_redirect_is_refused_not_followed(self, monkeypatch: pytest.MonkeyPatch):
        """Following it would send the credentials on to a host the URL check never saw."""
        jira = _jira(monkeypatch, "cloud", issues=0)
        jira.fail_next(302, headers={"Location": "https://evil.example/rest/api/2/myself"})

        with pytest.raises(JiraRequestError, match="redirects are not followed"):
            await _myself()

        assert len(jira.requests) == 1

    @pytest.mark.asyncio
    async def test_a_sign_in_page_instead_of_json_says_the_url_is_wrong(self, monkeypatch: pytest.MonkeyPatch):
        jira = _jira(monkeypatch, "cloud", issues=0)
        jira.fail_next(200, b"<html>Sign in</html>", headers={"Content-Type": "text/html; charset=utf-8"})

        with pytest.raises(JiraError, match="answered GET /rest/api/2/myself with text/html instead of JSON"):
            await _myself()

    @pytest.mark.asyncio
    async def test_a_garbled_error_body_still_names_status_and_path(self, monkeypatch: pytest.MonkeyPatch):
        jira = _jira(monkeypatch, "cloud", issues=0)
        jira.fail_next(400, b"not json")

        with pytest.raises(JiraRequestError, match=r"^Jira answered 400 Bad Request to GET /rest/api/2/myself$"):
            await _myself()

    @pytest.mark.asyncio
    async def test_a_project_key_cannot_walk_to_another_path(self, monkeypatch: pytest.MonkeyPatch):
        jira = _jira(monkeypatch, "cloud", issues=0)

        with pytest.raises(JiraRequestError):
            await _project("../myself")

        assert jira.requests[0].url.raw_path == b"/rest/api/2/project/..%2Fmyself"


class TestRetries:
    @pytest.mark.asyncio
    async def test_throttling_is_waited_out_for_as_long_as_jira_asks(self, monkeypatch: pytest.MonkeyPatch):
        jira = _jira(monkeypatch, "cloud", issues=0)
        jira.fail_next(429, headers={"Retry-After": "3"})

        assert (await _myself())["accountId"] == "bot-1"
        assert jira.waits == [3.0]

    @pytest.mark.asyncio
    async def test_retry_after_may_be_a_date(self, monkeypatch: pytest.MonkeyPatch):
        jira = _jira(monkeypatch, "cloud", issues=0)
        jira.fail_next(
            429, headers={"Retry-After": format_datetime(datetime.now(UTC) + timedelta(seconds=5), usegmt=True)}
        )

        await _myself()

        assert 0 < jira.waits[0] <= 5

    @pytest.mark.asyncio
    async def test_a_wait_longer_than_a_chat_can_take_fails_at_once(self, monkeypatch: pytest.MonkeyPatch):
        jira = _jira(monkeypatch, "cloud", issues=0)
        jira.fail_next(429, headers={"Retry-After": "120"})

        with pytest.raises(JiraRequestError, match="429 Too Many Requests .* Jira asks to wait 120 s"):
            await _myself()

        assert (len(jira.requests), jira.waits) == (1, [])

    @pytest.mark.asyncio
    async def test_a_gateway_error_is_retried_with_growing_waits(self, monkeypatch: pytest.MonkeyPatch):
        jira = _jira(monkeypatch, "cloud", issues=0)
        jira.fail_next(503, times=2)

        await _myself()

        assert jira.waits == [1.0, 2.0]

    @pytest.mark.asyncio
    async def test_a_gateway_error_that_persists_fails_after_the_last_attempt(self, monkeypatch: pytest.MonkeyPatch):
        jira = _jira(monkeypatch, "cloud", issues=0)
        jira.fail_next(503, times=JiraClient.MAX_ATTEMPTS)

        with pytest.raises(JiraRequestError, match="503 Service Unavailable"):
            await _myself()

        assert len(jira.requests) == JiraClient.MAX_ATTEMPTS

    @pytest.mark.asyncio
    async def test_a_client_error_is_not_retried(self, monkeypatch: pytest.MonkeyPatch):
        jira = _jira(monkeypatch, "cloud", issues=0)
        jira.fail_next(400, {"errorMessages": ["Bad"]})

        with pytest.raises(JiraRequestError):
            await _myself()

        assert len(jira.requests) == 1

    @pytest.mark.asyncio
    async def test_a_refused_connection_is_retried(self, monkeypatch: pytest.MonkeyPatch):
        jira = _jira(monkeypatch, "cloud", issues=0)
        jira.raise_next(httpx.ConnectError)

        assert (await _myself())["accountId"] == "bot-1"
        assert jira.waits == [1.0]

    @pytest.mark.asyncio
    async def test_a_slow_answer_is_not_retried_and_names_only_the_host(self, monkeypatch: pytest.MonkeyPatch):
        """A read that timed out may have reached Jira; retrying it would only make the chat wait longer."""
        jira = _jira(monkeypatch, "cloud", issues=0)
        jira.raise_next(httpx.ReadTimeout)

        with pytest.raises(JiraError, match=r"^Jira at acme.atlassian.net did not respond \(ReadTimeout\)\.$"):
            await _myself()

        assert len(jira.requests) == 1


class TestJqlProblems:
    @pytest.mark.asyncio
    @pytest.mark.parametrize("deployment", ["cloud", "data_center"])
    async def test_an_unknown_field_is_named(self, monkeypatch: pytest.MonkeyPatch, deployment: str):
        jira = _jira(monkeypatch, deployment, issues=1)
        jira.unknown_jql_fields = {"statuz"}

        async with JiraClient.connect(_connection(deployment)) as client:
            problems = await client.jql_problems(f'{_SCOPE} AND statuz = "Done"')

        assert problems == ["Field 'statuz' does not exist or you do not have permission to view it."]

    @pytest.mark.asyncio
    @pytest.mark.parametrize("deployment", ["cloud", "data_center"])
    async def test_a_valid_query_has_none(self, monkeypatch: pytest.MonkeyPatch, deployment: str):
        _jira(monkeypatch, deployment, issues=1)

        async with JiraClient.connect(_connection(deployment)) as client:
            assert await client.jql_problems(_SCOPE) == []

    @pytest.mark.asyncio
    async def test_data_center_failing_for_another_reason_is_not_taken_for_a_bad_query(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        jira = _jira(monkeypatch, "data_center", issues=1)
        jira.fail_next(401)

        with pytest.raises(JiraRequestError, match="401"):
            await _jql_problems("data_center", _SCOPE)


class TestProjectVersions:
    @pytest.mark.asyncio
    @pytest.mark.parametrize("deployment", ["cloud", "data_center"])
    async def test_every_version_of_a_project_is_listed(self, monkeypatch: pytest.MonkeyPatch, deployment: str):
        jira = _jira(monkeypatch, deployment, issues=1)
        jira.add_version("AAA", "1.0", released=True)
        jira.add_version("AAA", "1.1")

        async with JiraClient.connect(_connection(deployment)) as client:
            versions = await client.project_versions("AAA")

        assert [(version["name"], version["released"]) for version in versions] == [("1.0", True), ("1.1", False)]

    @pytest.mark.asyncio
    async def test_an_object_where_a_list_belongs_fails(self, monkeypatch: pytest.MonkeyPatch):
        jira = _jira(monkeypatch, "cloud", issues=1)
        jira.fail_next(200, {"values": []})

        with pytest.raises(JiraError, match="with a dict instead of a list"):
            await _versions("AAA")


async def _versions(project: str) -> list[dict]:
    async with JiraClient.connect(_connection("cloud")) as client:
        return await client.project_versions(project)
