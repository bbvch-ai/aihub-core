from typing import Annotated

from pydantic import Field
from swiss_ai_hub.core.events.agent import ControlEvent
from swiss_ai_hub.core.jira import JiraVersion


class VersionResolvedEvent(ControlEvent):
    """The message names exactly one release: the fix version carrying that name in each project that has it."""

    versions: Annotated[list[JiraVersion], Field(description="One version per project, all with the same name.")]

    @property
    def name(self) -> str:
        return self.versions[0].name
