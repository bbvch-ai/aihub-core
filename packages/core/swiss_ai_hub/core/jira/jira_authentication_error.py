from typing import Annotated

from swiss_ai_hub.core.jira.jira_error import JiraError


class JiraAuthenticationError(JiraError):
    """Jira refused the credentials: a wrong or expired token, or a Cloud token paired with another account's e-mail."""

    def __init__(
        self,
        base_url: Annotated[str, "The Jira the credentials were tried against"],
        status_code: Annotated[int, "401 or 403"],
    ):
        super().__init__(
            f"Jira rejected the credentials for {base_url} ({status_code}). Check the account e-mail and API token "
            "(Jira Cloud) or the personal access token (Jira Data Center)."
        )
        self.base_url = base_url
        self.status_code = status_code
