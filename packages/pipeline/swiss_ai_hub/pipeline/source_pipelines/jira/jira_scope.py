from typing import Annotated, Any, Self
from zoneinfo import ZoneInfo

from pydantic import BaseModel, Field

_SERVICE_DESK = "service_desk"


class JiraScope(BaseModel):
    """What the preflight learned about the account and the projects, which the sync needs again."""

    account_name: Annotated[str, Field(description="Display name of the account the credentials sign in as.")]
    time_zone: Annotated[str, Field(description="The zone Jira reads the account's JQL dates in.")] = "UTC"
    service_desk_projects: Annotated[
        list[str], Field(description="Configured projects that are Service Management projects.")
    ] = []

    @classmethod
    def from_answers(cls, account: dict[str, Any], projects: dict[str, dict[str, Any]]) -> Self:
        """From ``/myself`` and ``/project/{key}`` of every configured project."""
        return cls(
            account_name=account.get("displayName") or "this account",
            time_zone=account.get("timeZone") or "UTC",
            service_desk_projects=sorted(
                key for key, project in projects.items() if project.get("projectTypeKey") == _SERVICE_DESK
            ),
        )

    @property
    def zone(self) -> ZoneInfo:
        return ZoneInfo(self.time_zone)

    def is_service_desk(self, project: str) -> bool:
        return project in self.service_desk_projects
