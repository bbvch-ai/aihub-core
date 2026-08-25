from contextlib import ExitStack
from types import SimpleNamespace
from unittest.mock import AsyncMock

from pytest_bdd import given, parsers, scenarios, then, when
from swiss_ai_hub.core.events import BaseEvent
from swiss_ai_hub.core.events.agent import (
    MailBatchDraftedEvent,
    MailFetchedEvent,
    MailMovedEvent,
    UnreadMailListedEvent,
)
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.imap import DraftEmailSettings, ImapClientConfig
from swiss_ai_hub.core.testing import async_test

from swiss_ai_hub.agent.agents.imap_agent.configs.imap_agent_config import ImapAgentConfig
from swiss_ai_hub.agent.agents.imap_agent.events.draft_mail_start_event import DraftMailStartEvent
from swiss_ai_hub.agent.agents.imap_agent.events.read_mail_start_event import ReadMailStartEvent
from swiss_ai_hub.agent.agents.imap_agent.imap_agent import ImapAgent
from swiss_ai_hub.agent.imap.parsed_message import ParsedMessage
from swiss_ai_hub.agent.imap.tests.mail_doubles import infrastructure_patches, make_client
from swiss_ai_hub.agent.imap.tests.mail_doubles import summary as _summary
from swiss_ai_hub.agent.runners import AgentTestRunner

scenarios("./features/imap_agent.feature")


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


def _fake_llm_event() -> SimpleNamespace:
    return SimpleNamespace(chat_messages=[SimpleNamespace(content="Thanks, drafted reply body.")])


# --- read/move chain fixtures ---


@given("an ImapAgent runner with a mocked IMAP inbox", target_fixture="scenario")
def _() -> dict:
    return {"unread": [_summary("1")], "undrafted": [], "enable_move": False, "enable_draft": False}


@given("an ImapAgent runner with moving enabled and a mocked IMAP inbox", target_fixture="scenario")
def _moving_enabled() -> dict:
    return {"unread": [_summary("1")], "undrafted": [], "enable_move": True, "enable_draft": False}


@given("an ImapAgent runner with moving enabled and a missing target folder", target_fixture="scenario")
def _moving_into_missing_folder() -> dict:
    return {
        "unread": [_summary("1")],
        "undrafted": [],
        "enable_move": True,
        "enable_draft": False,
        "folder_created": True,
    }


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


async def _drive(agent_runner: AgentTestRunner, client: AsyncMock, start_event: BaseEvent) -> None:
    with ExitStack() as stack:
        for patcher in infrastructure_patches(client, _fake_llm_event()):
            stack.enter_context(patcher)
        async with agent_runner.test_run() as topic:
            await agent_runner.send_event_from_topic(start_event=start_event, topic=topic)


async def _run(scenario: dict, start_event: BaseEvent) -> AgentTestRunner:
    agent_runner = AgentTestRunner(
        agent_type=ImapAgent, agent_config=_config(scenario["enable_move"], scenario["enable_draft"])
    )
    client = make_client(scenario["unread"], scenario["undrafted"], scenario.get("folder_created", False))
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
    # The archived original is referenced alongside the attachments, never instead of them.
    assert events[0].original_message is not None
    assert events[0].original_message.content_type == "message/rfc822"


@then("no MailFetchedEvent was emitted")
def _(agent_runner: AgentTestRunner):
    assert len(_dedupe(agent_runner.get_events_of_class(MailFetchedEvent))) == 0


@then("a MailMovedEvent that moved the message was emitted")
def _(agent_runner: AgentTestRunner):
    events = _dedupe(agent_runner.get_events_of_class(MailMovedEvent))
    assert len(events) == 1
    assert events[0].target_folder == "Processed"
    assert events[0].folder_created is False


@then("a MailMovedEvent that records the created folder was emitted")
def _(agent_runner: AgentTestRunner):
    events = _dedupe(agent_runner.get_events_of_class(MailMovedEvent))
    assert len(events) == 1
    assert events[0].target_folder == "Processed"
    assert events[0].folder_created is True


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
    client = make_client(unread=[], undrafted=[_summary("11"), _summary("12")])

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
    client = make_client(unread=[], undrafted=[_summary("11")])
    client.mark_drafted = AsyncMock(side_effect=RuntimeError("STORE rejected"))

    await _drive(agent_runner, client, DraftMailStartEvent())

    assert client.append_draft.await_count == 1
    assert agent_runner.has_exception_event
    assert len(_dedupe(agent_runner.get_events_of_class(MailBatchDraftedEvent))) == 0
