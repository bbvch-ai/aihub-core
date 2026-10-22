import re
from collections.abc import Sequence
from typing import Annotated, Any

from swiss_ai_hub.core.infrastructure.jira.jira_settings import JiraSettings
from swiss_ai_hub.core.jira.jira_authentication_error import JiraAuthenticationError
from swiss_ai_hub.core.jira.jira_client import JiraClient
from swiss_ai_hub.core.jira.jira_configuration_error import JiraConfigurationError
from swiss_ai_hub.core.jira.jira_connection_config import JiraConnectionConfig
from swiss_ai_hub.core.jira.jira_invalid_query_error import JiraInvalidQueryError
from swiss_ai_hub.core.jira.jira_jql import JiraJql
from swiss_ai_hub.core.jira.jira_project_not_found_error import JiraProjectNotFoundError
from swiss_ai_hub.core.jira.jira_request_error import JiraRequestError
from swiss_ai_hub.core.jira.jira_ticket import JiraTicket
from swiss_ai_hub.core.network.source_host_guard import SourceHostGuard

_PROJECT_KEY = re.compile(r"^[A-Z][A-Z0-9_]*$")
_REFUSED_SIGN_IN = (401, 403)
_NOT_VISIBLE = (403, 404)


class JiraTicketSearch:
    """Every ticket of some projects that matches some JQL, read for an agent from its own connection config.

    It reads no agent configuration itself. Each mistake it checks for first would otherwise look like a release with
    no tickets: Jira answers a project the account cannot see, and on Cloud an invalid query, with zero results.
    """

    @classmethod
    async def find_tickets(
        cls,
        connection: Annotated[JiraConnectionConfig, "Where Jira is and how to sign in"],
        project_keys: Annotated[list[str], "Keys of the projects to read from; case and order do not matter"],
        clauses: Annotated[
            Sequence[str], "JQL every ticket must also match, e.g. an admin's filter and a version"
        ] = (),
    ) -> list[JiraTicket]:
        """Ordered by project and number. Checks, in this order: the configuration, the host, the credentials, each
        project, the query; so a mistake is reported as what it is, not as the next check failing."""
        projects = sorted({key.strip().upper() for key in project_keys if key.strip()})
        problems = connection.problems() + cls._key_problems(projects)
        if problems:
            raise JiraConfigurationError(problems)
        await cls._require_public_host(connection.base_url)
        jql = JiraJql.compose(projects, clauses)
        async with JiraClient.connect(connection) as client:
            account = await cls._signed_in_account(client, connection.base_url)
            for project in projects:
                await cls._require_visible(client, project, account)
            await cls._require_valid(client, jql)
            tickets = [
                cls._own_ticket(hit, projects)
                async for page in client.search(jql, JiraTicket.FIELDS, rendered=True, limit=connection.max_tickets)
                for hit in page
            ]
        return sorted(tickets, key=lambda ticket: (ticket.project, ticket.number))

    @staticmethod
    def _key_problems(projects: list[str]) -> list[str]:
        if not projects:
            return ["no project key is given"]
        invalid = [key for key in projects if not _PROJECT_KEY.match(key)]
        if invalid:
            return [f"{', '.join(invalid)} {'is' if len(invalid) == 1 else 'are'} not a Jira project key"]
        return []

    @staticmethod
    async def _require_public_host(base_url: str) -> None:
        """An agent administrator sets the URL, and agents reach the platform's own services."""
        try:
            await SourceHostGuard.require_public_async(
                base_url, JiraSettings().private_host_allow_list(), JiraSettings.ALLOW_LIST_VARIABLE
            )
        except ValueError as refused:
            raise JiraConfigurationError([str(refused)]) from refused

    @staticmethod
    async def _signed_in_account(client: JiraClient, base_url: str) -> str:
        """A 404 or a redirect here means the URL leads to a web server but not to Jira's REST API, e.g. a missing
        or wrong context path; Data Center redirects such a path to its own error page."""
        try:
            account = await client.myself()
        except JiraRequestError as refused:
            if refused.status_code in _REFUSED_SIGN_IN:
                raise JiraAuthenticationError(base_url, refused.status_code) from refused
            if refused.status_code == 404:
                raise JiraConfigurationError(
                    [
                        f"{base_url} has no Jira REST API (404 on {refused.path}); check the URL, including a Data "
                        "Center context path such as /jira"
                    ]
                ) from refused
            if 300 <= refused.status_code < 400:
                raise JiraConfigurationError([str(refused)]) from refused
            raise
        return account.get("displayName") or "this account"

    @staticmethod
    async def _require_visible(client: JiraClient, project: str, account: str) -> None:
        """Jira keeps answering a renamed project's old key, but its tickets carry the new one."""
        try:
            answer = await client.project(project)
        except JiraRequestError as refused:
            if refused.status_code not in _NOT_VISIBLE:
                raise
            raise JiraProjectNotFoundError(project, account) from refused
        if answer.get("key", project) != project:
            raise JiraProjectNotFoundError(project, account, renamed_to=answer["key"])

    @staticmethod
    async def _require_valid(client: JiraClient, jql: str) -> None:
        problems = await client.jql_problems(jql)
        if problems:
            raise JiraInvalidQueryError(problems)

    @staticmethod
    def _own_ticket(hit: dict[str, Any], projects: list[str]) -> JiraTicket:
        """The clauses are parenthesised, but a crafted one could still reach past them; a ticket of a project
        nobody configured must not reach an agent's answer."""
        ticket = JiraTicket.from_search_hit(hit)
        if ticket.project not in projects:
            raise JiraInvalidQueryError(
                [f"Jira returned {ticket.key}, which is outside the configured projects; check the JQL clauses"]
            )
        return ticket
