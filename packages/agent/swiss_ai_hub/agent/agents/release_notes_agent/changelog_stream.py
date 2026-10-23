from collections.abc import Sequence
from typing import Annotated

from swiss_ai_hub.core.displayers import EventDisplayer
from swiss_ai_hub.core.i18n import LocaleHandler

from swiss_ai_hub.agent.agents.release_notes_agent.changelog_entry import ChangelogEntry
from swiss_ai_hub.agent.agents.release_notes_agent.changelog_renderer import ChangelogRenderer
from swiss_ai_hub.agent.agents.release_notes_agent.changelog_section import ChangelogSection
from swiss_ai_hub.agent.agents.release_notes_agent.release_language import ReleaseLanguage


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
        link_tickets: Annotated[bool, "End each bullet with its tickets' keys, linked to them"],
        model_name: Annotated[str, "Model the chunks are attributed to"],
        shown: Annotated[str, "What an earlier step of the run already showed, which this stream continues"] = "",
    ):
        self._displayer = displayer
        self._t = t
        self._link_tickets = link_tickets
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

    async def add(self, entries: Annotated[Sequence[ChangelogEntry], "The next entries, in changelog order"]) -> None:
        pieces: list[str] = []
        for entry in entries:
            if entry.section != self._section:
                self._section = entry.section
                pieces.append(ChangelogRenderer.heading(entry.section, self._language, self._t))
            pieces.append(ChangelogRenderer.bullet(entry, self._link_tickets))
        await self._show("".join(pieces))

    async def _show(self, text: str) -> None:
        if text:
            await self._displayer.display_chunk(text, model_name=self._model_name)
            self._shown.append(text)
