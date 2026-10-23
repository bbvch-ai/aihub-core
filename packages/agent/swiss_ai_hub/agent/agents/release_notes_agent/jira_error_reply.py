from typing import Annotated, Self

from pydantic import BaseModel, Field
from swiss_ai_hub.core.i18n import LocaleHandler
from swiss_ai_hub.core.jira import (
    JiraAuthenticationError,
    JiraConfigurationError,
    JiraError,
    JiraInvalidQueryError,
    JiraProjectNotFoundError,
    JiraTooManyTicketsError,
)

_KEY = "agent.release_notes_agent.messages"


class JiraErrorReply(BaseModel):
    """A failed Jira read in the user's words, and in Jira's.

    The user reads one sentence in their language saying who can fix it; Jira's English detail, which names hosts,
    statuses and query problems, goes into a thought for the administrator who looks at the run.
    """

    message: Annotated[str, Field(description="What the user reads, in the run's language.")]
    detail: Annotated[str, Field(description="The error as the Jira client worded it, in English.")]

    @classmethod
    def from_error(
        cls,
        error: Annotated[JiraError, "What kept the read from completing"],
        t: Annotated[LocaleHandler, "Translations in the run's language"],
    ) -> Self:
        match error:
            case JiraAuthenticationError():
                message = t(f"{_KEY}.jira_authentication")
            case JiraProjectNotFoundError(renamed_to=str() as renamed_to):
                message = t(f"{_KEY}.jira_project_renamed", project=error.project_key, renamed=renamed_to)
            case JiraProjectNotFoundError():
                message = t(f"{_KEY}.jira_project_not_found", project=error.project_key)
            case JiraInvalidQueryError():
                message = t(f"{_KEY}.jira_invalid_query")
            case JiraTooManyTicketsError():
                message = t(f"{_KEY}.release_too_large", limit=error.limit)
            case JiraConfigurationError():
                message = t(f"{_KEY}.jira_configuration")
            case _:
                message = t(f"{_KEY}.jira_unavailable")
        return cls(message=message, detail=str(error))
