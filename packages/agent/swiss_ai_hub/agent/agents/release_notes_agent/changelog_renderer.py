import re
from typing import Annotated

from swiss_ai_hub.core.i18n import LocaleHandler

from swiss_ai_hub.agent.agents.release_notes_agent.changelog_entry import ChangelogEntry
from swiss_ai_hub.agent.agents.release_notes_agent.changelog_section import ChangelogSection
from swiss_ai_hub.agent.agents.release_notes_agent.release_language import ReleaseLanguage

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
        entry: Annotated[ChangelogEntry, "The entry to show"],
        link_tickets: Annotated[bool, "Show the keys of its tickets, linked to them"],
        keys_first: Annotated[bool, "Lead the bullet with the keys in bold brackets, instead of ending it with them"],
    ) -> str:
        """An entry is kept on its bullet's line, whatever line breaks the model wrote into it. One ticket per bullet
        leads with its key, as release notes templates do (**[ENG-12]** …); a merged entry can name a dozen, so its
        keys go last, the way changelogs reference their issues."""
        text = _SPACES.sub(" ", entry.text).strip()
        if not link_tickets:
            return f"- {text}\n"
        if keys_first:
            keys = ", ".join(f"[[{note.key}]({note.url})]" for note in entry.notes)
            return f"- **{keys}** {text}\n"
        keys = ", ".join(f"[{note.key}]({note.url})" for note in entry.notes)
        return f"- {text} ({keys})\n"
