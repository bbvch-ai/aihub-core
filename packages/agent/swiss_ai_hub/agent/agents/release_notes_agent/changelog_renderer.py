import re
from typing import Annotated

from swiss_ai_hub.core.i18n import LocaleHandler

from swiss_ai_hub.agent.agents.release_notes_agent.changelog_section import ChangelogSection
from swiss_ai_hub.agent.agents.release_notes_agent.release_language import ReleaseLanguage
from swiss_ai_hub.agent.agents.release_notes_agent.release_note import ReleaseNote

_SPACES = re.compile(r"\s+")
_KEY = "agent.release_notes_agent.changelog"


class ChangelogRenderer:
    """The markdown of a changelog, a piece at a time: each piece ends in a line break, so the pieces shown one after
    another read as one document."""

    @staticmethod
    def title(
        version: Annotated[str, "The version name as Jira spells it"],
        language: Annotated[ReleaseLanguage, "The language of the block the title opens"],
        t: Annotated[LocaleHandler, "Translations"],
    ) -> str:
        return f"## {t(f'{_KEY}.title', locale=language, version=version)}\n"

    @staticmethod
    def heading(
        section: Annotated[ChangelogSection, "The section that starts"],
        language: Annotated[ReleaseLanguage, "The language of the block"],
        t: Annotated[LocaleHandler, "Translations"],
    ) -> str:
        return f"\n### {t(f'{_KEY}.sections.{section}', locale=language)}\n\n"

    @staticmethod
    def bullet(
        note: Annotated[ReleaseNote, "The note to show"],
        show_ticket_keys: Annotated[bool, "Lead the bullet with the ticket key, linked to the ticket"],
    ) -> str:
        """A note is kept on its bullet's line, whatever line breaks the model wrote into it."""
        text = _SPACES.sub(" ", note.note).strip()
        if show_ticket_keys:
            return f"- [{note.key}]({note.url}): {text}\n"
        return f"- {text}\n"
