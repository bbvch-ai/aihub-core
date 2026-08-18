"""Test doubles for the IMAP client and mail store, shared by every blueprint that reads a mailbox.

Only the doubles that encode the ``ImapClient`` / ``MailStore`` contract live here, so two agent test suites cannot
drift apart on what the client looks like. Scenario-specific fixtures stay in the suite that uses them.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, patch

from swiss_ai_hub.core.events.agent import MailAttachmentRef, MailMessageRef, UnreadMailSummary
from swiss_ai_hub.core.imap import ImapClientConfig

from swiss_ai_hub.agent.imap.parsed_message import ParsedAttachment, ParsedMessage

FACTORY = "swiss_ai_hub.agent.imap.imap_client.ImapClientFactory.create"
STORE_ATTACHMENTS = "swiss_ai_hub.agent.imap.mail_store.MailStore.store_attachments"
STORE_MESSAGE = "swiss_ai_hub.agent.imap.mail_store.MailStore.store_message"
LLM_STREAM = "swiss_ai_hub.core.displayers.event_displayer.EventDisplayer.display_llm_stream"
COST_LLM = "swiss_ai_hub.core.generative_ai.resources.models.llm.lite_llm_base.LiteLLMBase.cost_reporting_llm"

ATTACHMENT_FILE_ID = "0d5f7a1c-3b2e-4c8d-9a6f-1e2d3c4b5a6f"
MESSAGE_FILE_ID = "1a2b3c4d-5e6f-4a7b-8c9d-0e1f2a3b4c5d"


def summary(uid: str, subject: str | None = None) -> UnreadMailSummary:
    return UnreadMailSummary(message_id=uid, sender="alice@test", subject=subject or f"Subject {uid}")


def parsed_message(
    message_id: str = "1", subject: str = "Quarterly report", body_text: str = "See attached."
) -> ParsedMessage:
    return ParsedMessage(
        message_id=message_id,
        sender="alice@test",
        subject=subject,
        rfc_message_id=f"<orig-{message_id}@test>",
        body_text=body_text,
        attachments=[ParsedAttachment(filename="report.pdf", content_type="application/pdf", content=b"%PDF-1.4")],
    )


def make_client(
    unread: list[UnreadMailSummary] | None = None,
    undrafted: list[UnreadMailSummary] | None = None,
    folder_created: bool = False,
) -> AsyncMock:
    """An ImapClient double whose every method matches the real client's signature and return shape."""
    client = AsyncMock()
    client.list_unread = AsyncMock(return_value=unread or [])
    client.move_message = AsyncMock(return_value=folder_created)
    client.fetch_message = AsyncMock(return_value=parsed_message())
    client.list_undrafted = AsyncMock(return_value=("$AiHubDrafted", undrafted or []))
    client.mark_drafted = AsyncMock()
    client.append_draft = AsyncMock(return_value=("[Gmail]/Drafts", "57"))
    return client


@asynccontextmanager
async def fake_create(client: AsyncMock, _config: ImapClientConfig) -> AsyncIterator[AsyncMock]:
    yield client


@asynccontextmanager
async def fake_cost_reporting_llm(*_args, **_kwargs) -> AsyncIterator[AsyncMock]:
    yield AsyncMock()


def stored_attachment_refs() -> list[MailAttachmentRef]:
    return [
        MailAttachmentRef(
            filename="report.pdf", content_type="application/pdf", file_id=ATTACHMENT_FILE_ID, size_bytes=8
        )
    ]


def stored_message_ref() -> MailMessageRef:
    return MailMessageRef(filename="1.eml", file_id=MESSAGE_FILE_ID, size_bytes=64)


def infrastructure_patches(client: AsyncMock, llm_event: object | None = None) -> tuple:
    """The IMAP factory, the mail store (attachments + archived original), and the LLM, all patched.

    ``llm_event`` is what a patched ``display_llm_stream`` returns; pass the shape the calling suite expects.
    """
    return (
        patch(FACTORY, side_effect=lambda config: fake_create(client, config)),
        patch(STORE_ATTACHMENTS, new=AsyncMock(return_value=stored_attachment_refs())),
        patch(STORE_MESSAGE, new=AsyncMock(return_value=stored_message_ref())),
        patch(COST_LLM, new=fake_cost_reporting_llm),
        patch(LLM_STREAM, new=AsyncMock(return_value=llm_event)),
    )
