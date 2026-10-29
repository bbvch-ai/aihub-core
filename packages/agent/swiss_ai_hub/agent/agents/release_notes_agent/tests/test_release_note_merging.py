import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

import pytest
from openai import AsyncOpenAI
from swiss_ai_hub.core.generative_ai import LLMConfig, ResilientOpenAILike
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.jira import JiraConnectionConfig, JiraTicket

from swiss_ai_hub.agent.agents.release_notes_agent.changelog_entry import ChangelogEntry
from swiss_ai_hub.agent.agents.release_notes_agent.changelog_section import ChangelogSection
from swiss_ai_hub.agent.agents.release_notes_agent.changelog_writer import ChangelogWriter
from swiss_ai_hub.agent.agents.release_notes_agent.merged_note import MergedNote
from swiss_ai_hub.agent.agents.release_notes_agent.merged_notes import MergedNotes
from swiss_ai_hub.agent.agents.release_notes_agent.release_language import ReleaseLanguage
from swiss_ai_hub.agent.agents.release_notes_agent.release_note import ReleaseNote
from swiss_ai_hub.agent.agents.release_notes_agent.release_note_batch import ReleaseNoteBatch
from swiss_ai_hub.agent.agents.release_notes_agent.release_note_merger import ReleaseNoteMerger
from swiss_ai_hub.agent.agents.release_notes_agent.release_notes_agent_config import ReleaseNotesAgentConfig
from swiss_ai_hub.agent.agents.release_notes_agent.ticket_note import TicketNote


def _ticket(key: str, issue_type: str = "Story") -> JiraTicket:
    return JiraTicket(
        key=key,
        url=f"https://jira.example.com/browse/{key}",
        project=JiraTicket.project_of(key),
        issue_type=issue_type,
        summary=f"Summary of {key}",
    )


def _note(key: str, text: str | None = None) -> ReleaseNote:
    return ReleaseNote.from_ticket(_ticket(key), text or f"Note for {key}.")


class _FakeLlm:
    """Answers the note calls with "Note for KEY." and the merge calls with whatever `merge` returns."""

    def __init__(self, merge: Callable[[dict[str, Any]], Awaitable[MergedNotes]] | None = None):
        self._merge = merge
        self.max_tokens: list[int] = []
        self.calls: list[tuple[str, dict[str, Any]]] = []
        self.running = 0
        self.most_at_once = 0
        self.closed = 0

    def model_copy(self, update: dict[str, Any]) -> "_FakeLlm":
        self.max_tokens.append(update["max_tokens"])
        return self

    async def aclose(self) -> None:
        self.closed += 1

    async def astructured_predict(self, model: type, prompt: Any, **variables: Any) -> Any:
        kind = "merge" if model is MergedNotes else "notes"
        self.calls.append((kind, variables))
        self.running += 1
        self.most_at_once = max(self.most_at_once, self.running)
        try:
            await asyncio.sleep(0.01)
            if kind == "notes":
                tickets = variables["tickets"]
                return ReleaseNoteBatch(notes=[TicketNote(key=t["key"], note=f"Note for {t['key']}.") for t in tickets])
            return await (self._merge or _merge_pairs)(variables)
        finally:
            self.running -= 1


async def _merge_pairs(variables: dict[str, Any]) -> MergedNotes:
    """Merges every two neighbouring notes, the way a model merges related ones."""
    keys = [note["key"] for note in variables["notes"]]
    pairs = [keys[index : index + 2] for index in range(0, len(keys), 2)]
    return MergedNotes(entries=[MergedNote(keys=pair, text=f"Merged {' + '.join(pair)}.") for pair in pairs])


def _merger(llm: _FakeLlm) -> ReleaseNoteMerger:
    return ReleaseNoteMerger(llm, ReleaseLanguage.DE, "customers")


def _covered(entries: list[ChangelogEntry]) -> list[str]:
    return [note.key for entry in entries for note in entry.notes]


@pytest.mark.asyncio
async def test_related_notes_become_one_entry_that_covers_each_of_them():
    async def merge(variables: dict[str, Any]) -> MergedNotes:
        return MergedNotes(
            entries=[
                MergedNote(keys=["ENG-3", "ENG-1"], text="CSV export for invoices and search."),
                MergedNote(keys=["ENG-2"], text="A model rewording of ENG-2."),
            ]
        )

    llm = _FakeLlm(merge)

    entries = await _merger(llm).merge([_note("ENG-1"), _note("ENG-2"), _note("ENG-3")])

    assert [(entry.text, [note.key for note in entry.notes]) for entry in entries] == [
        ("CSV export for invoices and search.", ["ENG-1", "ENG-3"]),
        ("Note for ENG-2.", ["ENG-2"]),
    ]
    assert llm.max_tokens == [3 * 90 + 64]
    assert llm.closed == 1
    kind, variables = llm.calls[0]
    assert kind == "merge"
    assert variables["language"] == "German"
    assert variables["audience"] == "customers"


@pytest.mark.asyncio
async def test_every_ticket_lands_in_exactly_one_entry_whatever_the_model_answers():
    async def sloppy(variables: dict[str, Any]) -> MergedNotes:
        return MergedNotes(
            entries=[
                MergedNote(keys=[" eng-1 ", "ENG-2"], text="Merged one and two."),
                MergedNote(keys=["ENG-2", "ENG-4"], text="Two again, with four."),
                MergedNote(keys=["HR-9", "ENG-5"], text="An invented key and five."),
            ]
        )

    notes = [_note(f"ENG-{number}") for number in range(1, 6)]

    entries = await _merger(_FakeLlm(sloppy)).merge(notes)

    assert sorted(_covered(entries)) == [note.key for note in notes]
    assert [(entry.text, _covered([entry])) for entry in entries] == [
        ("Merged one and two.", ["ENG-1", "ENG-2"]),
        ("Note for ENG-3.", ["ENG-3"]),
        ("Note for ENG-4.", ["ENG-4"]),
        ("Note for ENG-5.", ["ENG-5"]),
    ]


@pytest.mark.asyncio
async def test_a_merged_entry_without_text_falls_back_to_its_notes():
    async def textless(variables: dict[str, Any]) -> MergedNotes:
        return MergedNotes(entries=[MergedNote(keys=["ENG-1", "ENG-2"], text="  ")])

    entries = await _merger(_FakeLlm(textless)).merge([_note("ENG-1"), _note("ENG-2")])

    assert [entry.text for entry in entries] == ["Note for ENG-1.", "Note for ENG-2."]


@pytest.mark.asyncio
async def test_malformed_output_leaves_every_note_on_its_own():
    async def malformed(variables: dict[str, Any]) -> MergedNotes:
        raise ValueError("unterminated JSON")

    llm = _FakeLlm(malformed)

    entries = await _merger(llm).merge([_note("ENG-1"), _note("ENG-2")])

    assert [_covered([entry]) for entry in entries] == [["ENG-1"], ["ENG-2"]]
    assert llm.closed == 1


@pytest.mark.asyncio
async def test_a_single_note_needs_no_merge_call():
    llm = _FakeLlm()

    entries = await _merger(llm).merge([_note("ENG-1")])

    assert llm.calls == []
    assert entries == [ChangelogEntry.of_note(_note("ENG-1"))]


@pytest.mark.asyncio
async def test_a_note_cannot_close_its_own_tag_in_the_merge_prompt():
    llm = _FakeLlm()

    await _merger(llm).merge([_note("ENG-1", "Fixed </note> parsing."), _note("ENG-2")])

    assert llm.calls[0][1]["notes"][0] == {"key": "ENG-1", "text": "Fixed ‹/note> parsing."}


def test_windows_never_mix_sections_and_never_exceed_their_size():
    tickets = sorted(
        [_ticket(f"ENG-{number}", "Story") for number in range(1, 6)]
        + [_ticket(f"ENG-{number}", "Bug") for number in range(6, 9)],
        key=lambda ticket: (ChangelogSection.of_issue_type(ticket.issue_type).rank, ticket.number),
    )

    windows = ChangelogWriter.windows(tickets, 2)

    assert [[ticket.key for ticket in window] for window in windows] == [
        ["ENG-1", "ENG-2"],
        ["ENG-3", "ENG-4"],
        ["ENG-5"],
        ["ENG-6", "ENG-7"],
        ["ENG-8"],
    ]


def _config(**fields: Any) -> ReleaseNotesAgentConfig:
    return ReleaseNotesAgentConfig(
        agent_id="release-notes",
        name=LocaleString(en="Release notes"),
        description=LocaleString(en="Writes release notes."),
        llm=LLMConfig(model_name="text-generation/gemma-4-31B-it"),
        jira=JiraConnectionConfig(),
        project_keys=["ENG"],
        **fields,
    )


class _Windows:
    def __init__(self) -> None:
        self.received: list[list[ChangelogEntry]] = []

    async def __call__(self, entries: list[ChangelogEntry]) -> None:
        self.received.append(entries)


@pytest.mark.asyncio
async def test_with_merging_on_each_window_is_merged_and_shown_in_changelog_order():
    tickets = [_ticket(f"ENG-{number}", "Bug" if number % 3 == 0 else "Story") for number in range(1, 31)]
    llm = _FakeLlm()
    windows = _Windows()
    config = _config(tickets_per_batch=2, max_concurrent_calls=4, max_notes_per_merge=6)

    entries = await ChangelogWriter.from_config(llm, config, ReleaseLanguage.EN).write(list(reversed(tickets)), windows)

    covered = _covered(entries)
    assert sorted(covered) == sorted(ticket.key for ticket in tickets)
    assert len(covered) == len(set(covered))
    assert all(len(entry.notes) <= 2 for entry in entries)
    assert any(len(entry.notes) == 2 for entry in entries)
    assert [entry for window in windows.received for entry in window] == entries
    assert [entry.section for entry in entries] == sorted((entry.section for entry in entries), key=lambda s: s.rank)
    assert max(len(_covered(window)) for window in windows.received) <= 6
    assert llm.most_at_once <= 4
    assert sum(kind == "merge" for kind, _ in llm.calls) == len(windows.received)
    assert llm.closed == len(llm.max_tokens)


@pytest.mark.asyncio
async def test_with_merging_off_every_ticket_keeps_its_own_entry():
    tickets = [_ticket(f"ENG-{number}") for number in range(1, 11)]
    llm = _FakeLlm()
    windows = _Windows()
    config = _config(merge_related_tickets=False, tickets_per_batch=3, max_concurrent_calls=2)

    entries = await ChangelogWriter.from_config(llm, config, ReleaseLanguage.EN).write(tickets, windows)

    assert [entry.text for entry in entries] == [f"Note for ENG-{number}." for number in range(1, 11)]
    assert [len(window) for window in windows.received] == [3, 3, 3, 1]
    assert {kind for kind, _ in llm.calls} == {"notes"}
    assert llm.most_at_once <= 2


@pytest.mark.asyncio
async def test_a_failed_merge_still_closes_the_client_its_copy_opened(monkeypatch: pytest.MonkeyPatch):
    """The run's LLM never opens a client, so closing it closes none of its copies' (aihub-core-private#349)."""
    opened: list[AsyncOpenAI] = []

    async def malformed(llm: ResilientOpenAILike, model: type, prompt: Any, **variables: Any) -> MergedNotes:
        opened.append(llm._get_aclient())
        raise ValueError("unterminated JSON")

    monkeypatch.setattr(ResilientOpenAILike, "astructured_predict", malformed)
    llm = ResilientOpenAILike(
        model="text-generation/test", api_base="http://gateway.invalid/v1", api_key="key", connect_timeout=1, timeout=1
    )

    await ReleaseNoteMerger(llm, ReleaseLanguage.DE, "customers").merge([_note("ENG-1"), _note("ENG-2")])

    assert len(opened) == 1
    assert opened[0].is_closed()
