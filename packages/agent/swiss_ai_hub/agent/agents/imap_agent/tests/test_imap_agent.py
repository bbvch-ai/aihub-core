from collections.abc import AsyncIterator
from contextlib import ExitStack, asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from pytest_bdd import given, parsers, scenarios, then, when
from swiss_ai_hub.core.events import BaseEvent
from swiss_ai_hub.core.events.agent import (
    MailAttachmentRef,
    MailBatchDraftedEvent,
    MailFetchedEvent,
    MailMovedEvent,
    UnreadMailListedEvent,
    UnreadMailSummary,
)
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.imap import DraftEmailSettings, ImapClientConfig
from swiss_ai_hub.core.testing import async_test

from swiss_ai_hub.agent.agents.imap_agent.configs.imap_agent_config import ImapAgentConfig
from swiss_ai_hub.agent.agents.imap_agent.events.draft_mail_start_event import DraftMailStartEvent
from swiss_ai_hub.agent.agents.imap_agent.events.read_mail_start_event import ReadMailStartEvent
from swiss_ai_hub.agent.agents.imap_agent.imap_agent import ImapAgent
from swiss_ai_hub.agent.imap.parsed_message import ParsedAttachment, ParsedMessage
from swiss_ai_hub.agent.runners import AgentTestRunner

scenarios("./features/imap_agent.feature")

_FACTORY = "swiss_ai_hub.agent.imap.imap_client.ImapClientFactory.create"
_STORE = "swiss_ai_hub.agent.imap.mail_attachment_store.MailAttachmentStore.store"
_LLM_STREAM = "swiss_ai_hub.core.displayers.event_displayer.EventDisplayer.display_llm_stream"
_COST_LLM = "swiss_ai_hub.core.generative_ai.resources.models.llm.lite_llm_base.LiteLLMBase.cost_reporting_llm"
_FILE_ID = "0d5f7a1c-3b2e-4c8d-9a6f-1e2d3c4b5a6f"


def _config(enable_move: bool = False, enable_draft: bool = False) -> ImapAgentConfig:
    return ImapAgentConfig(
        agent_id="imap_agent",
        name=LocaleString(en="IMAP Agent"),
        description=LocaleString(en="Test agent"),
        imap=ImapClientConfig(
            host="imap.test",
            username="a@test",
            password="secret",
            enable_move=enable_move,
            processed_folder="Processed",
        ),
        draft=DraftEmailSettings(
            enable_draft=enable_draft,
            source_folder="Processed",
            batch_size=5,
            drafts_folder="Drafts",
            model_name="text-generation/test-model",
        ),
    )


def _summary(uid: str) -> UnreadMailSummary:
    return UnreadMailSummary(message_id=uid, sender="alice@test", subject=f"Subject {uid}")


def _make_client(unread: list[UnreadMailSummary], undrafted: list[UnreadMailSummary]) -> AsyncMock:
    client = AsyncMock()
    client.list_unread = AsyncMock(return_value=unread)
    client.fetch_message = AsyncMock(
        return_value=ParsedMessage(
            message_id="1",
            sender="alice@test",
            subject="Quarterly report",
            rfc_message_id="<orig-1@test>",
            body_text="See attached.",
            attachments=[ParsedAttachment(filename="report.pdf", content_type="application/pdf", content=b"%PDF-1.4")],
        )
    )
    client.list_undrafted = AsyncMock(return_value=("$AiHubDrafted", undrafted))
    client.mark_drafted = AsyncMock()
    client.append_draft = AsyncMock(return_value=("[Gmail]/Drafts", "57"))
    return client


@asynccontextmanager
async def _fake_create(client: AsyncMock, _config: ImapClientConfig) -> AsyncIterator[AsyncMock]:
    yield client


@asynccontextmanager
async def _fake_cost_reporting_llm(*_args, **_kwargs) -> AsyncIterator[AsyncMock]:
    yield AsyncMock()


def _fake_llm_event() -> SimpleNamespace:
    return SimpleNamespace(chat_messages=[SimpleNamespace(content="Thanks, drafted reply body.")])


# --- read/move chain fixtures ---


@given("an ImapAgent runner with a mocked IMAP inbox", target_fixture="scenario")
def _() -> dict:
    return {"unread": [_summary("1")], "undrafted": [], "enable_move": False, "enable_draft": False}


@given("an ImapAgent runner with moving enabled and a mocked IMAP inbox", target_fixture="scenario")
def _moving_enabled() -> dict:
    return {"unread": [_summary("1")], "undrafted": [], "enable_move": True, "enable_draft": False}


@given("an ImapAgent runner with an empty IMAP inbox", target_fixture="scenario")
def _empty() -> dict:
    return {"unread": [], "undrafted": [], "enable_move": False, "enable_draft": False}


# --- draft chain fixtures ---


@given("an ImapAgent runner with drafting enabled and undrafted mail in the source folder", target_fixture="scenario")
def _drafting_with_undrafted() -> dict:
    return {"unread": [], "undrafted": [_summary("11"), _summary("12")], "enable_move": False, "enable_draft": True}


@given("an ImapAgent runner with drafting enabled and no undrafted mail", target_fixture="scenario")
def _drafting_no_undrafted() -> dict:
    return {"unread": [], "undrafted": [], "enable_move": False, "enable_draft": True}


@given("an ImapAgent runner with drafting disabled", target_fixture="scenario")
def _drafting_disabled() -> dict:
    return {"unread": [], "undrafted": [_summary("11")], "enable_move": False, "enable_draft": False}


def _patches(client: AsyncMock) -> tuple:
    """The infrastructure patches shared by every draft/read test: the IMAP factory, the attachment store, and the
    LLM (cost-reporting client + stream)."""
    stored_refs = [
        MailAttachmentRef(filename="report.pdf", content_type="application/pdf", file_id=_FILE_ID, size_bytes=8)
    ]
    return (
        patch(_FACTORY, side_effect=lambda config: _fake_create(client, config)),
        patch(_STORE, new=AsyncMock(return_value=stored_refs)),
        patch(_COST_LLM, new=_fake_cost_reporting_llm),
        patch(_LLM_STREAM, new=AsyncMock(return_value=_fake_llm_event())),
    )


async def _drive(agent_runner: AgentTestRunner, client: AsyncMock, start_event: BaseEvent) -> None:
    with ExitStack() as stack:
        for patcher in _patches(client):
            stack.enter_context(patcher)
        async with agent_runner.test_run() as topic:
            await agent_runner.send_event_from_topic(start_event=start_event, topic=topic)


async def _run(scenario: dict, start_event: BaseEvent) -> AgentTestRunner:
    agent_runner = AgentTestRunner(
        agent_type=ImapAgent, agent_config=_config(scenario["enable_move"], scenario["enable_draft"])
    )
    client = _make_client(scenario["unread"], scenario["undrafted"])
    await _drive(agent_runner, client, start_event)
    return agent_runner


@when("the user triggers reading mail", target_fixture="agent_runner")
@async_test
async def _(scenario: dict) -> AgentTestRunner:
    return await _run(scenario, ReadMailStartEvent())


@when("the user triggers drafting", target_fixture="agent_runner")
@async_test
async def _(scenario: dict) -> AgentTestRunner:
    return await _run(scenario, DraftMailStartEvent())


def _dedupe(events: list[BaseEvent]) -> list[BaseEvent]:
    """ControlAndDisplayEvents are observed twice (JetStream + NATS Core) — deduplicate by event_id."""
    return list({e.event_id: e for e in events}.values())


@then("an UnreadMailListedEvent was emitted")
def _(agent_runner: AgentTestRunner):
    assert len(_dedupe(agent_runner.get_events_of_class(UnreadMailListedEvent))) == 1


@then("a MailFetchedEvent was emitted")
def _(agent_runner: AgentTestRunner):
    events = _dedupe(agent_runner.get_events_of_class(MailFetchedEvent))
    assert len(events) == 1
    assert events[0].attachments[0].filename == "report.pdf"


@then("no MailFetchedEvent was emitted")
def _(agent_runner: AgentTestRunner):
    assert len(_dedupe(agent_runner.get_events_of_class(MailFetchedEvent))) == 0


@then("a MailMovedEvent that moved the message was emitted")
def _(agent_runner: AgentTestRunner):
    events = _dedupe(agent_runner.get_events_of_class(MailMovedEvent))
    assert len(events) == 1
    assert events[0].target_folder == "Processed"


@then("no MailMovedEvent was emitted")
def _(agent_runner: AgentTestRunner):
    assert len(_dedupe(agent_runner.get_events_of_class(MailMovedEvent))) == 0


@then(parsers.parse("a MailBatchDraftedEvent with {count:d} drafts was emitted"))
def _(agent_runner: AgentTestRunner, count: int):
    events = _dedupe(agent_runner.get_events_of_class(MailBatchDraftedEvent))
    assert len(events) == 1
    assert events[0].count == count
    assert len(events[0].drafted) == count


@then("no MailBatchDraftedEvent was emitted")
def _(agent_runner: AgentTestRunner):
    assert len(_dedupe(agent_runner.get_events_of_class(MailBatchDraftedEvent))) == 0


@then("a StopEvent is present")
def _(agent_runner: AgentTestRunner):
    assert agent_runner.has_stop_event


@then("no ExceptionEvent is present")
def _(agent_runner: AgentTestRunner):
    assert not agent_runner.has_exception_event


# --- focused draft-chain tests (not BDD) ---


@async_test
async def test_marks_each_drafted_message_so_it_is_not_redrafted():
    """After drafting, every source message is flagged. A real server's UNKEYWORD/UNANSWERED search then excludes it
    on the next trigger (covered in test_imap_client) — here we lock in that each source is marked exactly once."""
    agent_runner = AgentTestRunner(agent_type=ImapAgent, agent_config=_config(enable_draft=True))
    client = _make_client(unread=[], undrafted=[_summary("11"), _summary("12")])

    async def _fetch(message_id: str, folder: str | None = None) -> ParsedMessage:
        return ParsedMessage(
            message_id=message_id, sender="alice@test", subject="Subject", rfc_message_id=f"<{message_id}@test>"
        )

    client.fetch_message = _fetch

    await _drive(agent_runner, client, DraftMailStartEvent())

    assert not agent_runner.has_exception_event
    assert client.mark_drafted.await_count == 2
    marked_uids = sorted(call.args[1] for call in client.mark_drafted.await_args_list)
    assert marked_uids == ["11", "12"]


@async_test
async def test_batch_aborts_when_marking_fails_after_appending():
    """At-least-once: the draft is appended before the source is flagged, so if marking fails the reply is already
    saved and the still-unflagged source is re-drafted next run rather than lost."""
    agent_runner = AgentTestRunner(agent_type=ImapAgent, agent_config=_config(enable_draft=True))
    client = _make_client(unread=[], undrafted=[_summary("11")])
    client.mark_drafted = AsyncMock(side_effect=RuntimeError("STORE rejected"))

    await _drive(agent_runner, client, DraftMailStartEvent())

    assert client.append_draft.await_count == 1
    assert agent_runner.has_exception_event
    assert len(_dedupe(agent_runner.get_events_of_class(MailBatchDraftedEvent))) == 0
