import pytest

from swiss_ai_hub.core.jira.jira_authentication_error import JiraAuthenticationError
from swiss_ai_hub.core.jira.jira_configuration_error import JiraConfigurationError
from swiss_ai_hub.core.jira.jira_connection_config import JiraConnectionConfig
from swiss_ai_hub.core.jira.jira_error import JiraError
from swiss_ai_hub.core.jira.jira_invalid_query_error import JiraInvalidQueryError
from swiss_ai_hub.core.jira.jira_jql import JiraJql
from swiss_ai_hub.core.jira.jira_project_not_found_error import JiraProjectNotFoundError
from swiss_ai_hub.core.jira.jira_ticket_search import JiraTicketSearch
from swiss_ai_hub.core.jira.jira_too_many_tickets_error import JiraTooManyTicketsError
from swiss_ai_hub.core.jira.tests.unit.fake_jira import FakeJira

_EDITIONS = ["cloud", "data_center"]


@pytest.fixture(autouse=True)
def _no_internal_host_allowed(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set explicitly, so a developer's own environment cannot make a test pass or fail."""
    monkeypatch.setenv("JIRA_ALLOWED_PRIVATE_HOSTS", "")


def _jira(monkeypatch: pytest.MonkeyPatch, deployment: str, keys: tuple[str, ...] = ("AAA-1", "AAA-2")) -> FakeJira:
    jira = FakeJira(deployment=deployment, page_size=2)
    for key in keys:
        jira.add_issue(key)
    jira.install(monkeypatch)
    return jira


def _connection(deployment: str = "cloud", **overrides: object) -> JiraConnectionConfig:
    values = {"base_url": "https://acme.atlassian.net", "deployment": deployment, "email": "bot@acme.test"}
    return JiraConnectionConfig(**{**values, "api_token": "s3cret-token", **overrides})


class TestTickets:
    @pytest.mark.asyncio
    @pytest.mark.parametrize("deployment", _EDITIONS)
    async def test_every_ticket_of_every_project_is_returned_across_pages(
        self, monkeypatch: pytest.MonkeyPatch, deployment: str
    ):
        _jira(monkeypatch, deployment, ("AAA-1", "BBB-1", "AAA-2", "BBB-2", "AAA-3"))

        tickets = await JiraTicketSearch.find_tickets(_connection(deployment), ["AAA", "BBB"])

        assert [ticket.key for ticket in tickets] == ["AAA-1", "AAA-2", "AAA-3", "BBB-1", "BBB-2"]

    @pytest.mark.asyncio
    async def test_a_ticket_carries_its_description_as_markdown(self, monkeypatch: pytest.MonkeyPatch):
        _jira(monkeypatch, "data_center", ("AAA-1",))

        [ticket] = await JiraTicketSearch.find_tickets(_connection("data_center"), ["AAA"])

        assert ticket.description == "## Description\n\nRendered text of AAA-1"

    @pytest.mark.asyncio
    async def test_project_keys_are_normalised_before_anything_is_asked(self, monkeypatch: pytest.MonkeyPatch):
        jira = _jira(monkeypatch, "cloud", ("AAA-1", "BBB-1"))

        await JiraTicketSearch.find_tickets(_connection(), [" bbb ", "AAA", "aaa"])

        assert jira.sent_jql() == ['(project in ("AAA", "BBB")) ORDER BY id ASC']

    @pytest.mark.asyncio
    @pytest.mark.parametrize("deployment", _EDITIONS)
    async def test_a_fix_version_from_a_chat_message_narrows_the_tickets(
        self, monkeypatch: pytest.MonkeyPatch, deployment: str
    ):
        jira = FakeJira(deployment=deployment)
        jira.add_issue("AAA-1", fixVersions=[{"name": "2.4.0"}])
        jira.add_issue("AAA-2", fixVersions=[{"name": "2.5.0"}])
        jira.install(monkeypatch)

        tickets = await JiraTicketSearch.find_tickets(
            _connection(deployment),
            ["AAA"],
            ['issuetype != "Sub-task"', f"fixVersion = {JiraJql.string_literal('2.4.0')}"],
        )

        assert [(ticket.key, ticket.fix_versions) for ticket in tickets] == [("AAA-1", ["2.4.0"])]


class TestDistinctErrors:
    """Wrong credentials, an unknown project and invalid JQL each say what they are (acceptance criterion 3)."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("deployment", _EDITIONS)
    async def test_wrong_credentials(self, monkeypatch: pytest.MonkeyPatch, deployment: str):
        _jira(monkeypatch, deployment).fail_next(401)
        connection = _connection(deployment)

        with pytest.raises(
            JiraAuthenticationError, match="Jira rejected the credentials for https://acme.atlassian.net"
        ):
            await JiraTicketSearch.find_tickets(connection, ["AAA"])

    @pytest.mark.asyncio
    @pytest.mark.parametrize("deployment", _EDITIONS)
    async def test_an_unknown_project(self, monkeypatch: pytest.MonkeyPatch, deployment: str):
        _jira(monkeypatch, deployment)
        connection = _connection(deployment)

        with pytest.raises(
            JiraProjectNotFoundError, match="Jira project ZZZ does not exist, or Release Bot cannot see it"
        ):
            await JiraTicketSearch.find_tickets(connection, ["AAA", "ZZZ"])

    @pytest.mark.asyncio
    @pytest.mark.parametrize("deployment", _EDITIONS)
    async def test_invalid_jql(self, monkeypatch: pytest.MonkeyPatch, deployment: str):
        """Cloud would answer this with no tickets at all; the query is checked before the search."""
        jira = _jira(monkeypatch, deployment)
        jira.unknown_jql_fields = {"statuz"}
        connection = _connection(deployment)

        with pytest.raises(JiraInvalidQueryError, match="Field 'statuz' does not exist") as refused:
            await JiraTicketSearch.find_tickets(connection, ["AAA"], ["statuz = Done"])

        assert refused.value.problems == ["Field 'statuz' does not exist or you do not have permission to view it."]
        assert jira.sent_jql() == []

    @pytest.mark.asyncio
    async def test_the_three_messages_differ(self, monkeypatch: pytest.MonkeyPatch):
        messages = set()
        for fail in ("credentials", "project", "jql"):
            with monkeypatch.context() as patched:
                jira = _jira(patched, "cloud")
                jira.unknown_jql_fields = {"statuz"}
                if fail == "credentials":
                    jira.fail_next(401)
                connection = _connection()
                projects = ["AAA", "ZZZ"] if fail == "project" else ["AAA"]
                with pytest.raises(JiraError) as refused:
                    await JiraTicketSearch.find_tickets(connection, projects, ["statuz = Done"])
            messages.add(f"{type(refused.value).__name__}: {refused.value}")

        assert len(messages) == 3

    @pytest.mark.asyncio
    @pytest.mark.parametrize("deployment", _EDITIONS)
    async def test_an_unknown_fix_version_is_named_by_jira(self, monkeypatch: pytest.MonkeyPatch, deployment: str):
        _jira(monkeypatch, deployment)
        connection = _connection(deployment)

        with pytest.raises(JiraInvalidQueryError, match="The value '9.9.9' does not exist for the field 'fixVersion'"):
            await JiraTicketSearch.find_tickets(connection, ["AAA"], ['fixVersion = "9.9.9"'])


class TestScope:
    @pytest.mark.asyncio
    async def test_a_value_crafted_to_widen_the_query_stays_one_value(self, monkeypatch: pytest.MonkeyPatch):
        jira = _jira(monkeypatch, "cloud")
        crafted = JiraJql.string_literal('2.4.0" OR project = HR OR fixVersion = "')
        connection = _connection()

        with pytest.raises(JiraInvalidQueryError, match="does not exist for the field 'fixVersion'"):
            await JiraTicketSearch.find_tickets(connection, ["AAA"], [f"fixVersion = {crafted}"])

        assert jira.sent_jql() == []

    @pytest.mark.asyncio
    @pytest.mark.parametrize("deployment", _EDITIONS)
    async def test_a_ticket_outside_the_configured_projects_fails_the_search(
        self, monkeypatch: pytest.MonkeyPatch, deployment: str
    ):
        jira = _jira(monkeypatch, deployment)
        jira.leaked_issue = jira.add_issue("HR-1")
        connection = _connection(deployment)

        with pytest.raises(JiraInvalidQueryError, match="Jira returned HR-1, which is outside the configured projects"):
            await JiraTicketSearch.find_tickets(connection, ["AAA"])

    @pytest.mark.asyncio
    async def test_a_renamed_project_names_its_new_key(self, monkeypatch: pytest.MonkeyPatch):
        jira = _jira(monkeypatch, "cloud")
        jira.renamed_projects = {"AAA": "NEW"}
        connection = _connection()

        with pytest.raises(JiraProjectNotFoundError, match="AAA has been renamed to NEW") as refused:
            await JiraTicketSearch.find_tickets(connection, ["AAA"])

        assert refused.value.renamed_to == "NEW"

    @pytest.mark.asyncio
    @pytest.mark.parametrize("deployment", _EDITIONS)
    async def test_more_tickets_than_allowed_fails_instead_of_cutting_the_list(
        self, monkeypatch: pytest.MonkeyPatch, deployment: str
    ):
        _jira(monkeypatch, deployment, tuple(f"AAA-{number}" for number in range(1, 6)))
        connection = _connection(deployment, max_tickets=3)

        with pytest.raises(JiraTooManyTicketsError):
            await JiraTicketSearch.find_tickets(connection, ["AAA"])


class TestConfiguration:
    @pytest.mark.asyncio
    async def test_missing_values_are_named_before_any_request(self, monkeypatch: pytest.MonkeyPatch):
        jira = _jira(monkeypatch, "cloud")
        connection = JiraConnectionConfig()

        with pytest.raises(JiraConfigurationError) as refused:
            await JiraTicketSearch.find_tickets(connection, [])

        assert refused.value.problems == [
            "the Jira URL is missing",
            "the token is missing",
            "Jira Cloud needs the e-mail of the account the API token belongs to",
            "no project key is given",
        ]
        assert jira.requests == []

    @pytest.mark.asyncio
    async def test_a_malformed_project_key_is_refused(self, monkeypatch: pytest.MonkeyPatch):
        _jira(monkeypatch, "cloud")
        connection = _connection()

        with pytest.raises(JiraConfigurationError, match="ENG-1 is not a Jira project key"):
            await JiraTicketSearch.find_tickets(connection, ["eng-1"])

    @pytest.mark.asyncio
    async def test_a_url_without_jira_behind_it_is_not_taken_for_wrong_credentials(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        _jira(monkeypatch, "data_center").fail_next(
            404, b"<html>Not Found</html>", headers={"Content-Type": "text/html"}
        )
        connection = _connection("data_center")

        with pytest.raises(JiraConfigurationError, match=r"has no Jira REST API \(404 on /rest/api/2/myself\)"):
            await JiraTicketSearch.find_tickets(connection, ["AAA"])

    @pytest.mark.asyncio
    async def test_a_url_jira_redirects_is_a_configuration_problem(self, monkeypatch: pytest.MonkeyPatch):
        """Data Center 11.3 answers a wrong context path with a redirect to its own error page."""
        _jira(monkeypatch, "data_center").fail_next(302, headers={"Location": "https://acme.atlassian.net/404"})
        connection = _connection("data_center")

        with pytest.raises(JiraConfigurationError, match="302 Found .* redirects are not followed"):
            await JiraTicketSearch.find_tickets(connection, ["AAA"])

    @pytest.mark.asyncio
    async def test_order_by_is_refused_before_any_request(self, monkeypatch: pytest.MonkeyPatch):
        jira = _jira(monkeypatch, "cloud")
        connection = _connection()

        with pytest.raises(JiraInvalidQueryError, match="must not contain ORDER BY"):
            await JiraTicketSearch.find_tickets(connection, ["AAA"], ["status = Done ORDER BY created"])

        assert jira.requests == []


class TestHostGuard:
    @pytest.mark.asyncio
    async def test_an_internal_host_is_refused_before_any_request(self, monkeypatch: pytest.MonkeyPatch):
        jira = _jira(monkeypatch, "data_center")
        connection = _connection("data_center", base_url="http://litellm:4000")

        with pytest.raises(
            JiraConfigurationError, match="An operator can allow it with JIRA_ALLOWED_PRIVATE_HOSTS"
        ) as refused:
            await JiraTicketSearch.find_tickets(connection, ["AAA"])

        assert jira.requests == []
        assert str(refused.value).endswith("JIRA_ALLOWED_PRIVATE_HOSTS.")

    @pytest.mark.asyncio
    async def test_a_host_the_deployment_allows_is_read(self, monkeypatch: pytest.MonkeyPatch):
        _jira(monkeypatch, "data_center")
        monkeypatch.setenv("JIRA_ALLOWED_PRIVATE_HOSTS", "localhost")

        tickets = await JiraTicketSearch.find_tickets(
            _connection("data_center", base_url="http://localhost:8094"), ["AAA"]
        )

        assert len(tickets) == 2
