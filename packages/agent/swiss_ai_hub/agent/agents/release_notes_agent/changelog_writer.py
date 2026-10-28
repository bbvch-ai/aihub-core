import itertools
from collections.abc import Awaitable, Callable, Sequence
from typing import Annotated, Self

from swiss_ai_hub.core.generative_ai import ResilientOpenAILike
from swiss_ai_hub.core.jira import JiraTicket

from swiss_ai_hub.agent.agents.release_notes_agent.changelog_entry import ChangelogEntry
from swiss_ai_hub.agent.agents.release_notes_agent.changelog_section import ChangelogSection
from swiss_ai_hub.agent.agents.release_notes_agent.ordered_batches import OrderedBatches
from swiss_ai_hub.agent.agents.release_notes_agent.release_language import ReleaseLanguage
from swiss_ai_hub.agent.agents.release_notes_agent.release_note_merger import ReleaseNoteMerger
from swiss_ai_hub.agent.agents.release_notes_agent.release_note_writer import ReleaseNoteWriter
from swiss_ai_hub.agent.agents.release_notes_agent.release_notes_agent_config import ReleaseNotesAgentConfig


class ChangelogWriter:
    """Writes a release's changelog entries a window of tickets at a time, each window handed on in changelog order.

    A window holds tickets of one section only, since related notes are merged within a section. Merging needs a
    window's notes complete, so with merging on a window spans many tickets and windows run one after another, each
    writing its notes with all the run's model calls: two windows side by side halved the write speed of each, and the
    first text reached the chat after 39 s for 120 tickets, past the 30 s the bots wait for a chunk. With merging off a
    window is one batch of tickets. Either way a chat sees a window as soon as it and the ones before it are done.
    """

    def __init__(
        self,
        writer: Annotated[ReleaseNoteWriter, "Writes the note of each ticket"],
        merger: Annotated[ReleaseNoteMerger | None, "Merges related notes; None keeps one entry per ticket"],
        window_size: Annotated[int, "Tickets per window"],
        windows_at_once: Annotated[int, "Windows written at the same time"],
    ):
        self._writer = writer
        self._merger = merger
        self._window_size = window_size
        self._windows_at_once = windows_at_once

    @classmethod
    def from_config(
        cls,
        llm: Annotated[ResilientOpenAILike, "The model writing and merging the notes"],
        config: Annotated[ReleaseNotesAgentConfig, "The profile"],
        language: Annotated[ReleaseLanguage, "The language this answer is written in"],
    ) -> Self:
        if not config.merge_related_tickets:
            writer = ReleaseNoteWriter(
                llm, language, config.audience, config.tickets_per_batch, 1, config.max_description_chars
            )
            return cls(writer, None, config.tickets_per_batch, config.max_concurrent_calls)
        writer = ReleaseNoteWriter(
            llm,
            language,
            config.audience,
            config.tickets_per_batch,
            config.max_concurrent_calls,
            config.max_description_chars,
        )
        merger = ReleaseNoteMerger(llm, language, config.audience)
        return cls(writer, merger, config.max_notes_per_merge, 1)

    async def write(
        self,
        tickets: Annotated[Sequence[JiraTicket], "Every ticket of the release"],
        on_window: Annotated[Callable[[list[ChangelogEntry]], Awaitable[None]], "Receives each window, in order"],
    ) -> list[ChangelogEntry]:
        """Every entry, ordered by section and by the project and number of its first ticket."""
        ordered = sorted(tickets, key=ReleaseNoteWriter.changelog_order)
        windows = self.windows(ordered, self._window_size)
        written = await OrderedBatches.run(windows, self._write_window, on_window, self._windows_at_once)
        return [entry for window in written for entry in window]

    @staticmethod
    def windows(
        tickets: Annotated[Sequence[JiraTicket], "Tickets in changelog order"],
        size: Annotated[int, "Tickets per window at most"],
    ) -> list[list[JiraTicket]]:
        def section(ticket: JiraTicket) -> ChangelogSection:
            return ChangelogSection.of_issue_type(ticket.issue_type)

        return [
            list(window)
            for _, in_section in itertools.groupby(tickets, key=section)
            for window in itertools.batched(in_section, size)
        ]

    async def _write_window(self, tickets: list[JiraTicket]) -> list[ChangelogEntry]:
        notes = await self._writer.write(tickets)
        if self._merger is None:
            return [ChangelogEntry.of_note(note) for note in notes]
        return await self._merger.merge(notes)
