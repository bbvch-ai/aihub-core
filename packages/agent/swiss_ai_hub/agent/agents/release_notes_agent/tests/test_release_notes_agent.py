"""The blueprint end to end on the real dispatcher: a chat message in, a changelog or a plain reply out.

Needs the dev stack (NATS + Valkey) but neither Jira nor a model: the ticket search, the notes model and the
conversation's own model calls (meta-question detection, title, follow-ups) are stubbed. Marked self_hosted so the
lean CI skips it.
"""

from collections.abc import Iterator
from contextlib import asynccontextmanager
from typing import Any
from unittest.mock import patch

import pytest
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from swiss_ai_hub.core.events.agent import (
    ChunkEvent,
    LLMStopEvent,
    Message,
    MetaQuestionDetectedEvent,
    NotAMetaQuestionEvent,
    ThoughtEvent,
    UserMessageEvent,
)
from swiss_ai_hub.core.generative_ai import LLMConfig
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.jira import (
    JiraAuthenticationError,
    JiraConnectionConfig,
    JiraError,
    JiraTicket,
    JiraTicketSearch,
    JiraTooManyTicketsError,
    JiraVersion,
)
from swiss_ai_hub.core.testing import async_test
from swiss_ai_hub.core.testing.auth_utils import fake_user

from swiss_ai_hub.agent.agents.release_notes_agent import ReleaseNotesAgent, ReleaseNotesAgentConfig
from swiss_ai_hub.agent.agents.release_notes_agent.events.release_notes_written_event import ReleaseNotesWrittenEvent
from swiss_ai_hub.agent.agents.release_notes_agent.events.version_resolved_event import VersionResolvedEvent
from swiss_ai_hub.agent.agents.release_notes_agent.merged_note import MergedNote
from swiss_ai_hub.agent.agents.release_notes_agent.merged_notes import MergedNotes
from swiss_ai_hub.agent.agents.release_notes_agent.release_language import ReleaseLanguage
from swiss_ai_hub.agent.agents.release_notes_agent.release_note_batch import ReleaseNoteBatch
from swiss_ai_hub.agent.agents.release_notes_agent.ticket_note import TicketNote
from swiss_ai_hub.agent.runners.agent_test_runner import AgentTestRunner

pytestmark = pytest.mark.self_hosted

_CONVERSATION = "swiss_ai_hub.agent.capabilities.conversation.conversation"
_CONVERSATION_FIELDS = "swiss_ai_hub.agent.capabilities.conversation.conversation_fields"

_VERSIONS = [
    JiraVersion(id="10000", name="1.0", project="ENG", released=True),
    JiraVersion(id="10001", name="2.0", project="ENG"),
    JiraVersion(id="10002", name="2.0", project="SD"),
]
_TYPES = ["Story", "Bug", "Improvement", "Task"]
_TICKETS = [
    JiraTicket(
        key=key,
        url=f"https://jira.example.com/browse/{key}",
        project=JiraTicket.project_of(key),
        issue_type=_TYPES[index % 4],
        summary=f"Summary of {key}",
        description=f"What {key} changes.",
    )
    for index, key in enumerate([*(f"ENG-{number}" for number in range(1, 13)), "SD-1", "SD-2", "SD-3"])
]


class _FakeJira:
    def __init__(self, tickets: list[JiraTicket], versions_error: JiraError | None, tickets_error: JiraError | None):
        self.tickets = tickets
        self.versions_error = versions_error
        self.tickets_error = tickets_error
        self.version_lookups: list[list[str]] = []
        self.searches: list[tuple[JiraConnectionConfig, list[str], list[str]]] = []

    async def find_versions(self, connection: JiraConnectionConfig, project_keys: list[str]) -> list[JiraVersion]:
        self.version_lookups.append(project_keys)
        if self.versions_error:
            raise self.versions_error
        return _VERSIONS

    async def find_tickets(
        self, connection: JiraConnectionConfig, project_keys: list[str], clauses: Any = ()
    ) -> list[JiraTicket]:
        self.searches.append((connection, project_keys, list(clauses)))
        if self.tickets_error:
            raise self.tickets_error
        return self.tickets


class _FakeNotesLlm:
    """Writes "Note for KEY." per ticket, merges every two neighbouring notes of a section, and prefixes the target
    language when translating."""

    def model_copy(self, update: dict[str, Any]) -> "_FakeNotesLlm":
        return self

    async def aclose(self) -> None:
        pass

    async def astructured_predict(self, model: type, prompt: Any, **variables: Any) -> ReleaseNoteBatch | MergedNotes:
        if model is MergedNotes:
            keys = [note["key"] for note in variables["notes"]]
            pairs = [keys[index : index + 2] for index in range(0, len(keys), 2)]
            return MergedNotes(entries=[MergedNote(keys=pair, text=f"Merged {' + '.join(pair)}.") for pair in pairs])
        if "tickets" in variables:
            notes = [
                TicketNote(key=ticket["key"], note=f"Note for {ticket['key']}.") for ticket in variables["tickets"]
            ]
        else:
            notes = [TicketNote(key=n["key"], note=f"{variables['target']}: {n['text']}") for n in variables["notes"]]
        return ReleaseNoteBatch(notes=notes)


class _Platform:
    def __init__(self) -> None:
        self.follow_up_answers: list[list[ChatMessage]] = []
        self.meta = False
        self.jira = _FakeJira(_TICKETS, None, None)


@pytest.fixture
def platform(monkeypatch: pytest.MonkeyPatch) -> Iterator[_Platform]:
    stubbed = _Platform()

    async def detect(*, user_query: str, **_: Any) -> MetaQuestionDetectedEvent | NotAMetaQuestionEvent:
        if stubbed.meta:
            return MetaQuestionDetectedEvent(user_query=user_query, category="capabilities", reasoning="forced")
        return NotAMetaQuestionEvent(reasoning="forced normal")

    async def answer_meta_question(**_: Any) -> LLMStopEvent:
        return LLMStopEvent(output_messages=[Message.from_string(role="assistant", content="I write release notes.")])

    async def generate_title(chat_messages, llm_config, displayer, t, thread_context, user) -> None:
        return None

    async def generate_follow_up_questions(chat_messages, llm_config, displayer, t, user) -> None:
        stubbed.follow_up_answers.append(chat_messages)

    @asynccontextmanager
    async def notes_llm(self, displayer, extra_headers=None, user=None):
        yield _FakeNotesLlm()

    monkeypatch.setattr(f"{_CONVERSATION}.do_detect_meta_question", detect)
    monkeypatch.setattr(f"{_CONVERSATION}.do_answer_meta_question", answer_meta_question)
    monkeypatch.setattr(f"{_CONVERSATION}.generate_title", generate_title)
    monkeypatch.setattr(f"{_CONVERSATION_FIELDS}.usable_input_budget", lambda models: None)
    monkeypatch.setattr(LLMConfig, "cost_reporting_llm", notes_llm)
    monkeypatch.setattr(JiraTicketSearch, "find_versions", lambda *args: stubbed.jira.find_versions(*args))
    monkeypatch.setattr(JiraTicketSearch, "find_tickets", lambda *args: stubbed.jira.find_tickets(*args))
    with patch(
        f"{_CONVERSATION}.generate_follow_up_questions", autospec=True, side_effect=generate_follow_up_questions
    ):
        yield stubbed


def _config(**overrides: Any) -> ReleaseNotesAgentConfig:
    return ReleaseNotesAgentConfig(
        agent_id="release_notes_test",
        name=LocaleString(en="Test Release Notes"),
        description=LocaleString(en="Writes release notes."),
        llm=LLMConfig(model_name="text-generation/gemma-4-31B-it"),
        jira=JiraConnectionConfig(base_url="https://jira.example.com", deployment="data_center", api_token="secret"),
        project_keys=["ENG", "SD"],
        **overrides,
    )


async def _run(message: str, config: ReleaseNotesAgentConfig) -> AgentTestRunner:
    runner = AgentTestRunner(agent_type=ReleaseNotesAgent, agent_config=config)
    start = UserMessageEvent(
        messages=[ChatMessage(content=message, role=MessageRole.USER)], user=fake_user(), locale="en"
    )
    async with runner.test_run(delay_before_stop=30) as topic:
        await runner.send_event_from_topic(topic=topic, start_event=start)
    assert runner.has_stop_event, "the run did not end"
    assert not runner.has_exception_event
    return runner


def _answer(runner: AgentTestRunner) -> str:
    """The text the run ended on, checked against what the chat was streamed."""
    stops = {stop.event_id: stop for stop in runner.get_events_of_class(LLMStopEvent)}
    assert len(stops) == 1, "a control-and-display event is observed on both subjects, but once per id"
    text = next(iter(stops.values())).output_messages[0].content
    streamed = "".join(chunk.content for chunk in runner.get_events_of_class(ChunkEvent, exact=True))
    assert streamed == text
    return text


def _thoughts(runner: AgentTestRunner) -> str:
    return "\n".join(thought.reasoning_content for thought in runner.get_events_of_class(ThoughtEvent))


@async_test
async def test_every_ticket_of_the_release_gets_a_bullet_in_its_section(platform: _Platform):
    runner = await _run("Release notes for “2.0”, please", _config())

    answer = _answer(runner)
    assert answer.startswith("## Release notes 2.0\n")
    for ticket in _TICKETS:
        assert answer.count(f"[{ticket.key}]({ticket.url})") == 1, f"{ticket.key} must be in exactly one bullet"
    assert "- Merged ENG-1 + ENG-5. ([ENG-1](https://jira.example.com/browse/ENG-1), " in answer
    assert "- Note for ENG-12. ([ENG-12](https://jira.example.com/browse/ENG-12))\n" in answer
    assert answer.count("\n- ") == 8
    sections = [answer.index(f"### {heading}") for heading in ("New features", "Fixes", "Improvements", "Other")]
    assert sections == sorted(sections)
    connection, projects, clauses = platform.jira.searches[0]
    assert connection.max_tickets == 300
    assert projects == ["ENG", "SD"]
    assert clauses == ["", "fixVersion in (10001, 10002)"]
    assert runner.has_event_of_class(VersionResolvedEvent)
    assert "Read 15 tickets of fix version 2.0 from Jira." in _thoughts(runner)
    assert "15 notes were merged into 8 bullets." in _thoughts(runner)
    assert platform.follow_up_answers[0][-1].content == answer


@async_test
async def test_without_merging_every_ticket_keeps_a_bullet_of_its_own(platform: _Platform):
    runner = await _run("Release notes for 2.0", _config(merge_related_tickets=False))

    answer = _answer(runner)
    for ticket in _TICKETS:
        assert f"- **[[{ticket.key}]({ticket.url})]** Note for {ticket.key}.\n" in answer
    assert "Merged" not in answer
    assert "were merged" not in _thoughts(runner)


@async_test
async def test_each_further_language_follows_as_a_block_of_its_own(platform: _Platform):
    config = _config(translate_into=[ReleaseLanguage.DE, ReleaseLanguage.EN], link_tickets=False)

    runner = await _run("release notes for 2.0", config)

    answer = _answer(runner)
    english, german = answer.split("\n## Versionshinweise 2.0\n")
    assert english.count("\n- ") == german.count("\n- ") == 8
    assert "\n### Neue Funktionen\n\n- German: Merged ENG-1 + ENG-5.\n" in german
    assert "[ENG-1]" not in answer
    written = runner.get_events_of_class(ReleaseNotesWrittenEvent)[0]
    assert written.shown == english
    assert platform.follow_up_answers[0][-1].content == english, "follow-ups are grounded on the written language"


@async_test
async def test_a_language_the_message_asks_for_replaces_the_profiles(platform: _Platform):
    config = _config(translate_into=[ReleaseLanguage.DE])

    runner = await _run("Release notes for 2.0 in French", config)

    answer = _answer(runner)
    assert answer.startswith("## Notes de version 2.0\n")
    assert "Versionshinweise" not in answer
    assert "Release notes 2.0" not in answer
    assert "Writing in Français, as the message asks." in _thoughts(runner)
    assert runner.get_events_of_class(VersionResolvedEvent)[0].languages == [ReleaseLanguage.FR]


@pytest.mark.parametrize(
    ("message", "expected"),
    [
        (
            "write the release notes",
            "Which release should I write notes for? Name a fix version, for example: 2.0, 1.0.",
        ),
        ("compare 1.0 and 2.0", "Your message names several releases: 1.0, 2.0."),
        ("release notes for 2.5", "I found no fix version 2.5 in ENG, SD. Did you mean: 2.0"),
    ],
)
@async_test
async def test_a_message_without_exactly_one_known_version_is_answered_before_jira_is_searched(
    platform: _Platform, message: str, expected: str
):
    runner = await _run(message, _config())

    assert expected in _answer(runner)
    assert platform.jira.searches == []
    assert platform.follow_up_answers, "a reply still ends with follow-ups"


@async_test
async def test_a_release_without_tickets_says_so(platform: _Platform):
    platform.jira.tickets = []

    runner = await _run("notes for 2.0", _config(extra_jql="labels = customer"))

    assert _answer(runner) == (
        "I found no tickets for fix version 2.0 in ENG, SD, so there is nothing to write release notes about."
    )
    assert platform.jira.searches[0][2] == ["labels = customer", "fixVersion in (10001, 10002)"]


@async_test
async def test_a_release_over_the_cap_is_refused_in_plain_words(platform: _Platform):
    platform.jira.tickets_error = JiraTooManyTicketsError(300, 412)

    runner = await _run("notes for 2.0", _config())

    assert "This release has more than 300 tickets" in _answer(runner)
    assert "The search matches 412 tickets, more than the 300 read at once" in _thoughts(runner)


@async_test
async def test_a_jira_that_refuses_the_token_is_reported_without_its_details_in_the_answer(platform: _Platform):
    platform.jira.versions_error = JiraAuthenticationError("https://jira.example.com", 401)

    runner = await _run("notes for 2.0", _config())

    answer = _answer(runner)
    assert "Jira rejected this assistant's credentials" in answer
    assert "jira.example.com" not in answer
    assert "Jira rejected the credentials for https://jira.example.com (401)" in _thoughts(runner)
    assert platform.jira.searches == []


@async_test
async def test_a_question_about_the_assistant_reads_nothing_from_jira(platform: _Platform):
    platform.meta = True

    runner = await _run("What can you do?", _config())

    assert platform.jira.version_lookups == []
    assert platform.jira.searches == []
    assert not runner.has_event_of_class(VersionResolvedEvent)
