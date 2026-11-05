from typing import Annotated, Self

from pydantic import BaseModel, Field

from swiss_ai_hub.agent.agents.release_notes_agent.changelog_section import ChangelogSection
from swiss_ai_hub.agent.agents.release_notes_agent.release_note import ReleaseNote


class ChangelogEntry(BaseModel):
    """One changelog bullet: the note of one ticket, or one text for several related tickets merged into it."""

    section: Annotated[ChangelogSection, Field(description="The section every ticket of the entry belongs to.")]
    text: Annotated[str, Field(description="The text of the bullet.")]
    notes: Annotated[
        list[ReleaseNote], Field(min_length=1, description="The notes of the tickets it covers, in changelog order.")
    ]
    untranslated: Annotated[
        bool, Field(description="Whether the text stays in the writing language because its translation failed.")
    ] = False

    @classmethod
    def of_note(cls, note: Annotated[ReleaseNote, "The note of one ticket"]) -> Self:
        return cls(section=note.section, text=note.note, notes=[note])

    @property
    def key(self) -> str:
        """The first ticket's key, which names the entry in a model call."""
        return self.notes[0].key
