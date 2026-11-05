from typing import Annotated

from pydantic import Field
from swiss_ai_hub.core.events.agent import ControlEvent
from swiss_ai_hub.core.jira import JiraVersion

from swiss_ai_hub.agent.agents.release_notes_agent.release_language import ReleaseLanguage


class VersionResolvedEvent(ControlEvent):
    """The message names exactly one release: the fix version carrying that name in each project that has it."""

    versions: Annotated[list[JiraVersion], Field(description="One version per project, all with the same name.")]
    languages: Annotated[
        list[ReleaseLanguage],
        Field(
            min_length=1,
            description="The languages of this answer, writing language first: those the message asks for, else the "
            "profile's.",
        ),
    ]

    @property
    def name(self) -> str:
        return self.versions[0].name

    @property
    def writing_language(self) -> ReleaseLanguage:
        """Events keep an enum field's value, not the member, once they are read back from the stream."""
        return ReleaseLanguage(self.languages[0])

    @property
    def translation_targets(self) -> list[ReleaseLanguage]:
        return [ReleaseLanguage(language) for language in self.languages[1:]]
