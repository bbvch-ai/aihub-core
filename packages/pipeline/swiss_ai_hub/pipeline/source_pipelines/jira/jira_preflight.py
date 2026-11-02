from typing import Annotated, Any

from swiss_ai_hub.core.infrastructure import StructuredPipelineSettings
from swiss_ai_hub.core.network import SourceHostGuard

from swiss_ai_hub.pipeline.resources.jira.jira_client import JiraClient
from swiss_ai_hub.pipeline.resources.jira.jira_request_error import JiraRequestError
from swiss_ai_hub.pipeline.source_pipelines.jira.jira_options import JiraOptions
from swiss_ai_hub.pipeline.source_pipelines.jira.jira_scope import JiraScope

_ALLOW_LIST_VARIABLE = "STRUCTURED_PIPELINE_ALLOWED_PRIVATE_HOSTS"
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
    ) -> JiraScope:
        """Returns what the sync needs again: the account's time zone and which projects are service desks. The host
        is checked first, so no request reaches an internal one."""
        SourceHostGuard.require_public(
            options.base_url,
            StructuredPipelineSettings().private_host_allow_list(),
            _ALLOW_LIST_VARIABLE,
        )
        account = cls._signed_in_account(client, options.base_url)
        name = account.get("displayName") or "this account"
        projects = {project: cls._require_visible(client, project, name) for project in options.projects()}
        if options.jql.strip():
            cls._require_valid(client, options.jql.strip())
        return JiraScope.from_answers(account, projects)

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
    def _require_visible(client: JiraClient, project: str, account: str) -> dict[str, Any]:
        """Jira keeps answering a renamed project's old key, but its issues carry the new one."""
        try:
            answer = client.project(project)
        except JiraRequestError as refused:
            if refused.status_code not in _NOT_VISIBLE:
                raise
            raise ValueError(f"Jira project {project} does not exist, or {account} cannot see it.") from refused
        if answer.get("key", project) != project:
            raise ValueError(
                f"Jira project {project} has been renamed to {answer['key']}; change the database's project keys."
            )
        return answer

    @staticmethod
    def _require_valid(client: JiraClient, jql: str) -> None:
        problems = client.jql_problems(jql)
        if problems:
            raise ValueError(f"The JQL clause is invalid: {'; '.join(problems)}")
