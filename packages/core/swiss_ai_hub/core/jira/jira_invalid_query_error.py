from typing import Annotated

from swiss_ai_hub.core.jira.jira_error import JiraError


class JiraInvalidQueryError(JiraError):
    """The JQL is malformed or names something Jira does not know, such as a field or a fix version.

    Raised before the search, because Jira Cloud answers an invalid query with no tickets instead of an error.
    """

    def __init__(self, problems: Annotated[list[str], "Jira's own words for each problem"]):
        super().__init__(f"The JQL query is invalid: {'; '.join(problems)}")
        self.problems = problems
