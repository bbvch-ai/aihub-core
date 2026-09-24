from typing import Annotated, Self

from pydantic import BaseModel, Field

from swiss_ai_hub.api.routes.incident.github_issue_client import GitHubIssueClient


class IncidentAvailabilityDTO(BaseModel):
    """Whether this deployment files reports at all.

    Answered with 200 on every deployment, unlike the form and submit endpoints, so the UI can
    decide whether to draw the report button without a 404 that the shell's global error handler
    would toast at a user who has not done anything yet.
    """

    enabled: Annotated[bool, Field(description="True when an incident repository is configured")]

    @classmethod
    def from_client(cls, client: Annotated[GitHubIssueClient | None, "Issue client, absent when unconfigured"]) -> Self:
        return cls(enabled=client is not None)
