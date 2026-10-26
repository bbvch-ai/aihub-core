"""#1951's acceptance criteria against a real Jira Cloud site and a real Jira Data Center. Read-only.

Each edition is configured by an env file with ``JIRA_URL``, ``JIRA_DEPLOYMENT``, ``JIRA_EMAIL`` and ``JIRA_TOKEN``,
the format the pipeline's seed tool reads; an edition whose file is missing is skipped. Seed both sites first with
``packages/pipeline/playground/jira_seed`` (projects ENG and SD, including ``--bulk 120`` in ENG, so a search spans
more than one page of 100). Run from ``packages/core``:

    JIRA_LIVE_ENV_FILES=~/.jira-seed/cloud.env,~/.jira-seed/dc11.env \
        uv run pytest -m integration swiss_ai_hub/core/jira/tests/integration
"""

import os
from pathlib import Path
from urllib.parse import urlsplit

import httpx
import pytest
from dotenv import dotenv_values

from swiss_ai_hub.core.jira.jira_authentication_error import JiraAuthenticationError
from swiss_ai_hub.core.jira.jira_client import JiraClient
from swiss_ai_hub.core.jira.jira_connection_config import JiraConnectionConfig
from swiss_ai_hub.core.jira.jira_invalid_query_error import JiraInvalidQueryError
from swiss_ai_hub.core.jira.jira_jql import JiraJql
from swiss_ai_hub.core.jira.jira_project_not_found_error import JiraProjectNotFoundError
from swiss_ai_hub.core.jira.jira_ticket import JiraTicket
from swiss_ai_hub.core.jira.jira_ticket_search import JiraTicketSearch

_DEFAULT_ENV_FILES = "~/.jira-seed/cloud.env,~/.jira-seed/dc11.env"
_PROJECTS = ["ENG", "SD"]
_SEEDED = 'labels = "aihub-seed"'


def _env_files() -> list[Path]:
    listed = os.environ.get("JIRA_LIVE_ENV_FILES", _DEFAULT_ENV_FILES)
    return [Path(path.strip()).expanduser() for path in listed.split(",") if path.strip()]


@pytest.fixture(params=_env_files(), ids=lambda path: path.stem)
def connection(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch) -> JiraConnectionConfig:
    """Read with dotenv_values, never into os.environ, so the token reaches nothing but the connection."""
    if not request.param.exists():
        pytest.skip(f"{request.param} not found")
    env = dotenv_values(request.param)
    monkeypatch.setenv("JIRA_ALLOWED_PRIVATE_HOSTS", urlsplit(env["JIRA_URL"]).hostname or "")
    return JiraConnectionConfig(
        base_url=env["JIRA_URL"],
        deployment=env.get("JIRA_DEPLOYMENT") or "cloud",
        email=env.get("JIRA_EMAIL") or "",
        api_token=env["JIRA_TOKEN"],
    )


async def _jira_count(connection: JiraConnectionConfig, jql: str) -> int:
    """Jira's own count, asked outside the client under test."""
    cloud = connection.deployment == "cloud"
    async with httpx.AsyncClient(
        base_url=f"{connection.base_url.rstrip('/')}/",
        auth=httpx.BasicAuth(connection.email, connection.api_token) if cloud else None,
        headers={} if cloud else {"Authorization": f"Bearer {connection.api_token}"},
    ) as http:
        if cloud:
            return (await http.post("rest/api/3/search/approximate-count", json={"jql": jql})).json()["count"]
        return (await http.get("rest/api/2/search", params={"jql": jql, "maxResults": 0})).json()["total"]


@pytest.mark.asyncio
async def test_every_matching_ticket_is_returned_across_pages(connection: JiraConnectionConfig):
    tickets = await JiraTicketSearch.find_tickets(connection, _PROJECTS, [_SEEDED])

    assert len(tickets) > connection.page_size, "seed more than one page of tickets first (see the module docstring)"
    assert len({ticket.key for ticket in tickets}) == len(tickets)
    assert len(tickets) == await _jira_count(connection, f'project in ("ENG", "SD") AND {_SEEDED}')


@pytest.mark.asyncio
async def test_small_pages_add_up_to_the_same_tickets(connection: JiraConnectionConfig):
    small_pages = connection.model_copy(update={"page_size": 7})
    pages = []
    async with JiraClient.connect(small_pages) as client:
        async for page in client.search(JiraJql.compose(_PROJECTS, [_SEEDED]), JiraTicket.FIELDS):
            pages.append(page)

    assert len(pages) > 1
    assert sum(len(page) for page in pages) == len(
        await JiraTicketSearch.find_tickets(connection, _PROJECTS, [_SEEDED])
    )


@pytest.mark.asyncio
async def test_descriptions_are_readable_text(connection: JiraConnectionConfig):
    [ticket] = await JiraTicketSearch.find_tickets(connection, ["ENG"], ['labels = "aihub-case-rich-formatting"'])

    assert ticket.description.startswith("## Steps to reproduce\n\n1. Open the login page")
    assert "| Browser | Firefox 131 |" in ticket.description
    assert '"type"' not in ticket.description


@pytest.mark.asyncio
async def test_a_fix_version_returns_its_tickets_with_their_components(connection: JiraConnectionConfig):
    version = JiraJql.string_literal("1.0")
    tickets = await JiraTicketSearch.find_tickets(connection, _PROJECTS, [_SEEDED, f"fixVersion = {version}"])

    assert {ticket.project for ticket in tickets} == {"ENG", "SD"}
    assert all(ticket.fix_versions == ["1.0"] and ticket.components == ["API", "Frontend"] for ticket in tickets)


@pytest.mark.asyncio
async def test_wrong_credentials_unknown_project_and_invalid_jql_each_say_what_they_are(
    connection: JiraConnectionConfig,
):
    wrong_token = connection.model_copy(update={"api_token": "wrong-token"})
    with pytest.raises(JiraAuthenticationError) as wrong_credentials:
        await JiraTicketSearch.find_tickets(wrong_token, _PROJECTS)
    with pytest.raises(JiraProjectNotFoundError) as unknown_project:
        await JiraTicketSearch.find_tickets(connection, ["ENG", "ZZZ"])
    with pytest.raises(JiraInvalidQueryError) as invalid_jql:
        await JiraTicketSearch.find_tickets(connection, _PROJECTS, ["statuz = Done"])

    assert unknown_project.value.project_key == "ZZZ"
    assert invalid_jql.value.problems == ["Field 'statuz' does not exist or you do not have permission to view it."]
    assert len({str(wrong_credentials.value), str(unknown_project.value), str(invalid_jql.value)}) == 3
    assert connection.api_token not in str(wrong_credentials.value)


@pytest.mark.asyncio
async def test_the_versions_of_both_projects_are_listed(connection: JiraConnectionConfig):
    versions = await JiraTicketSearch.find_versions(connection, _PROJECTS)

    assert {version.project for version in versions} == {"ENG", "SD"}
    assert {"1.0", "2.0"} <= {version.name for version in versions if version.project == "ENG"}


@pytest.mark.asyncio
async def test_a_release_found_by_its_version_id_returns_every_ticket(connection: JiraConnectionConfig):
    """Release 2.0 is seeded with `seed --release 2.0` and spans more than one page of 100."""
    versions = [
        version for version in await JiraTicketSearch.find_versions(connection, _PROJECTS) if version.name == "2.0"
    ]

    tickets = await JiraTicketSearch.find_tickets(
        connection, _PROJECTS, ['labels = "aihub-case-release"', JiraJql.fix_version_clause(versions)]
    )

    assert len(tickets) == 120
    assert {ticket.issue_type for ticket in tickets} >= {"Bug", "Story", "Task"}
