from typing import Annotated

from pydantic import BaseModel, Field
from swiss_ai_hub.core.jira import JiraVersion

from swiss_ai_hub.agent.agents.release_notes_agent.version_match_outcome import VersionMatchOutcome


class VersionMatch(BaseModel):
    """The release a message names, or what to tell the user when it names none, or more than one."""

    outcome: Annotated[VersionMatchOutcome, Field(description="Whether exactly one version name was found.")]
    versions: Annotated[
        list[JiraVersion],
        Field(description="FOUND: every version carrying the name, one per project that has it."),
    ] = []
    names: Annotated[list[str], Field(description="SEVERAL: the version names the message mentions.")] = []
    requested: Annotated[
        str | None, Field(description="UNKNOWN: the version-like word of the message no version is named.")
    ] = None
    suggestions: Annotated[list[str], Field(description="UNKNOWN: names close to the requested one.")] = []
    recent: Annotated[
        list[str], Field(description="UNKNOWN and MISSING: names of the newest versions that are not archived.")
    ] = []

    @property
    def name(self) -> str:
        """The version name as Jira spells it; only for FOUND."""
        return self.versions[0].name
