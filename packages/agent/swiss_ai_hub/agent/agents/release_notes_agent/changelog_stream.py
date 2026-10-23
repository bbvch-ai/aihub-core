from collections.abc import Sequence
from typing import Annotated

from swiss_ai_hub.core.displayers import EventDisplayer
from swiss_ai_hub.core.i18n import LocaleHandler

from swiss_ai_hub.agent.agents.release_notes_agent.changelog_renderer import ChangelogRenderer
from swiss_ai_hub.agent.agents.release_notes_agent.changelog_section import ChangelogSection
from swiss_ai_hub.agent.agents.release_notes_agent.release_language import ReleaseLanguage
from swiss_ai_hub.agent.agents.release_notes_agent.release_note import ReleaseNote


class ChangelogStream:
    """Shows the changelog in the chat as it is written, and keeps exactly the text shown.

    The run ends on that text: the API appends whatever part of the stop event's text extends the chunks it streamed,
    which recovers a lost chunk only when the stop text starts with the streamed text to the character. A block per
    language, each starting with its own title and its first section.
    """

    def __init__(
        self,
        displayer: Annotated[EventDisplayer, "Where the chunks go"],
        t: Annotated[LocaleHandler, "Translations"],
        show_ticket_keys: Annotated[bool, "Lead each bullet with its ticket key, linked to the ticket"],
        model_name: Annotated[str, "Model the chunks are attributed to"],
        shown: Annotated[str, "What an earlier step of the run already showed, which this stream continues"] = "",
    ):
        self._displayer = displayer
        self._t = t
        self._show_ticket_keys = show_ticket_keys
        self._model_name = model_name
        self._shown: list[str] = [shown] if shown else []
        self._language = ReleaseLanguage.EN
        self._section: ChangelogSection | None = None

    @property
    def text(self) -> str:
        return "".join(self._shown)

    async def begin(
        self,
        language: Annotated[ReleaseLanguage, "The language of the block that starts"],
        version: Annotated[str, "The version name as Jira spells it"],
    ) -> None:
        self._language = language
        self._section = None
        separator = "\n" if self._shown else ""
        await self._show(separator + ChangelogRenderer.title(version, language, self._t))

    async def add(self, notes: Annotated[Sequence[ReleaseNote], "The next notes, in changelog order"]) -> None:
        pieces: list[str] = []
        for note in notes:
            if note.section != self._section:
                self._section = note.section
                pieces.append(ChangelogRenderer.heading(note.section, self._language, self._t))
            pieces.append(ChangelogRenderer.bullet(note, self._show_ticket_keys))
        await self._show("".join(pieces))

    async def _show(self, text: str) -> None:
        if text:
            await self._displayer.display_chunk(text, model_name=self._model_name)
            self._shown.append(text)
