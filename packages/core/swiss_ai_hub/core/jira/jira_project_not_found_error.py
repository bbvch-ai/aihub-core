from typing import Annotated

from swiss_ai_hub.core.jira.jira_error import JiraError


class JiraProjectNotFoundError(JiraError):
    """A configured project Jira does not answer for: it does not exist, the account may not see it (Jira cannot tell
    the two apart), or it was renamed and only its old key still answers."""

    def __init__(
        self,
        project_key: Annotated[str, "The configured key"],
        account: Annotated[str, "Display name of the account the credentials sign in as"],
        renamed_to: Annotated[str | None, "The project's current key, when Jira answered with another one"] = None,
    ):
        if renamed_to:
            message = (
                f"Jira project {project_key} has been renamed to {renamed_to}; change the configured project keys."
            )
        else:
            message = f"Jira project {project_key} does not exist, or {account} cannot see it."
        super().__init__(message)
        self.project_key = project_key
        self.renamed_to = renamed_to
