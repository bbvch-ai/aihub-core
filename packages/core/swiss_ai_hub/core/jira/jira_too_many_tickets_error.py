from typing import Annotated

from swiss_ai_hub.core.jira.jira_error import JiraError


class JiraTooManyTicketsError(JiraError):
    """The search matches more tickets than one read may return; the caller narrows the query instead of working on
    a list cut short."""

    def __init__(
        self,
        limit: Annotated[int, "How many tickets one read may return"],
        counted: Annotated[int | None, "How many Jira counted; None when Jira gives no count, as Cloud's search"],
    ):
        if counted is None:
            message = f"The search matches more than the {limit} tickets read at once; narrow the query."
        else:
            message = f"The search matches {counted} tickets, more than the {limit} read at once; narrow the query."
        super().__init__(message)
        self.limit = limit
        self.counted = counted
