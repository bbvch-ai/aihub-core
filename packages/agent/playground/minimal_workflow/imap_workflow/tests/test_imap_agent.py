from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, patch

import pytest
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from pytest_bdd import given, scenarios, then, when
from swiss_ai_hub.core.events import BaseEvent
from swiss_ai_hub.core.events.agent import (
    MailAttachmentRef,
    MailFetchedEvent,
    UnreadMailListedEvent,
    UnreadMailSummary,
    UserMessageEvent,
)
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.imap import ImapClientConfig
from swiss_ai_hub.core.testing import async_test
from swiss_ai_hub.core.testing.auth_utils import fake_user

from playground.minimal_workflow.imap_workflow.imap_agent import ImapAgent
from playground.minimal_workflow.imap_workflow.imap_agent_config import ImapAgentConfig
from swiss_ai_hub.agent.imap.parsed_message import ParsedAttachment, ParsedMessage
from swiss_ai_hub.agent.runners import AgentTestRunner

scenarios("./features/imap_agent.feature")

_FACTORY = "swiss_ai_hub.agent.imap.imap_client.ImapClientFactory.create"
_STORE = "swiss_ai_hub.agent.imap.mail_attachment_store.MailAttachmentStore.store"
_FILE_ID = "0d5f7a1c-3b2e-4c8d-9a6f-1e2d3c4b5a6f"


def _config() -> ImapAgentConfig:
    return ImapAgentConfig(
        agent_id="imap_agent",
        name=LocaleString(en="IMAP Agent"),
        description=LocaleString(en="Test agent"),
        imap=ImapClientConfig(host="imap.test", username="a@test", password="secret"),
    )


def _make_client(unread: list[UnreadMailSummary]) -> AsyncMock:
    client = AsyncMock()
    client.list_unread = AsyncMock(return_value=unread)
    client.fetch_message = AsyncMock(
        return_value=ParsedMessage(
            message_id="1",
            sender="alice@test",
            subject="Quarterly report",
            body_text="See attached.",
            attachments=[ParsedAttachment(filename="report.pdf", content_type="application/pdf", content=b"%PDF-1.4")],
        )
    )
    return client


@asynccontextmanager
async def _fake_create(client: AsyncMock, _config: ImapClientConfig) -> AsyncIterator[AsyncMock]:
    yield client


@pytest.fixture
def agent_runner() -> AgentTestRunner:
    return AgentTestRunner(agent_type=ImapAgent, agent_config=_config())


@given("an ImapAgent runner with a mocked IMAP inbox", target_fixture="unread_mail")
def _() -> list[UnreadMailSummary]:
    return [UnreadMailSummary(message_id="1", sender="alice@test", subject="Quarterly report")]


@given("an ImapAgent runner with an empty IMAP inbox", target_fixture="unread_mail")
def _empty() -> list[UnreadMailSummary]:
    return []


@when("the user asks to read mail")
@async_test
async def _(agent_runner: AgentTestRunner, unread_mail: list[UnreadMailSummary]):
    client = _make_client(unread_mail)

    def create_side_effect(config: ImapClientConfig):
        return _fake_create(client, config)

    stored_refs = [
        MailAttachmentRef(filename="report.pdf", content_type="application/pdf", file_id=_FILE_ID, size_bytes=8)
    ]

    with (
        patch(_FACTORY, side_effect=create_side_effect),
        patch(_STORE, new=AsyncMock(return_value=stored_refs)),
    ):
        async with agent_runner.test_run() as topic:
            await agent_runner.send_event_from_topic(
                start_event=UserMessageEvent(
                    messages=[ChatMessage(content="read my mail", role=MessageRole.USER)],
                    user=fake_user(),
                ),
                topic=topic,
            )


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


@then("a StopEvent is present")
def _(agent_runner: AgentTestRunner):
    assert agent_runner.has_stop_event


@then("no ExceptionEvent is present")
def _(agent_runner: AgentTestRunner):
    assert not agent_runner.has_exception_event
