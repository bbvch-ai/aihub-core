from typing import Annotated

from swiss_ai_hub.core.jira.jira_error import JiraError


class JiraConfigurationError(JiraError):
    """The connection or the projects cannot be used as configured, found before or at the first request: a missing
    value, a host inside the platform, or a URL that does not lead to Jira's REST API."""

    def __init__(self, problems: Annotated[list[str], "Each problem, worded for the administrator who configured it"]):
        joined = "; ".join(problem.rstrip(".") for problem in problems)
        super().__init__(f"The Jira connection cannot be used: {joined}.")
        self.problems = problems
