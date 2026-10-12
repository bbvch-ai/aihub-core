from typing import Annotated, Any

from swiss_ai_hub.pipeline.resources.jira.jira_client import JiraClient
from swiss_ai_hub.pipeline.resources.jira.jira_request_error import JiraRequestError
from swiss_ai_hub.pipeline.source_pipelines.jira.jira_options import JiraOptions

_REFUSED_SIGN_IN = (401, 403)
_NOT_VISIBLE = (403, 404)


class JiraPreflight:
    """Checks a configuration against Jira before a sync reads or a listing removes anything.

    Each mistake it catches would otherwise pass silently: Jira answers a project the account cannot see, and on
    Cloud an invalid JQL clause, with no issues at all, and an empty listing removes that project's files. Failing
    here also keeps the message ours, instead of one dlt wraps around the first failed request.
    """

    @classmethod
    def check(
        cls,
        client: Annotated[JiraClient, "Client built from the configuration being checked"],
        options: Annotated[JiraOptions, "The configuration, already checked for missing values"],
    ) -> dict[str, Any]:
        """Returns the account the credentials sign in as, whose time zone Jira reads JQL dates in."""
        account = cls._signed_in_account(client, options.base_url)
        for project in options.projects():
            cls._require_visible(client, project, account.get("displayName") or "this account")
        if options.jql.strip():
            cls._require_valid(client, options.jql.strip())
        return account

    @staticmethod
    def _signed_in_account(client: JiraClient, base_url: str) -> dict[str, Any]:
        try:
            return client.myself()
        except JiraRequestError as refused:
            if refused.status_code not in _REFUSED_SIGN_IN:
                raise
            raise ValueError(
                f"Jira rejected the credentials for {base_url} ({refused.status_code}). Check the account e-mail and "
                "API token (Jira Cloud) or the personal access token (Jira Data Center)."
            ) from refused

    @staticmethod
    def _require_visible(client: JiraClient, project: str, account: str) -> None:
        try:
            client.project(project)
        except JiraRequestError as refused:
            if refused.status_code not in _NOT_VISIBLE:
                raise
            raise ValueError(f"Jira project {project} does not exist, or {account} cannot see it.") from refused

    @staticmethod
    def _require_valid(client: JiraClient, jql: str) -> None:
        problems = client.jql_problems(jql)
        if problems:
            raise ValueError(f"The JQL clause is invalid: {'; '.join(problems)}")
