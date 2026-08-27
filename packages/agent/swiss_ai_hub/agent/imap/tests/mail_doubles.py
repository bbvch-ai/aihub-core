"""Test doubles for the IMAP client and mail store, shared by every blueprint that reads a mailbox.

Only the doubles that encode the ``ImapClient`` / ``MailStore`` contract live here, so two agent test suites cannot
drift apart on what the client looks like. Scenario-specific fixtures stay in the suite that uses them.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from email.message import EmailMessage
from email.policy import default as default_policy
from unittest.mock import AsyncMock, patch

from swiss_ai_hub.core.events.agent import MailAttachmentRef, MailMessageRef, UnreadMailSummary
from swiss_ai_hub.core.imap import ImapClientConfig

from swiss_ai_hub.agent.imap.parsed_message import ParsedAttachment, ParsedMessage

FACTORY = "swiss_ai_hub.agent.imap.imap_client.ImapClientFactory.create"
STORE_ATTACHMENTS = "swiss_ai_hub.agent.imap.mail_store.MailStore.store_attachments"
STORE_MESSAGE = "swiss_ai_hub.agent.imap.mail_store.MailStore.store_message"
LOAD_MESSAGE = "swiss_ai_hub.agent.imap.mail_store.MailStore.load_message"
LOAD_ATTACHMENT = "swiss_ai_hub.agent.imap.mail_store.MailStore.load_attachment"
LOADER_FOR_FILE = (
    "swiss_ai_hub.core.generative_ai.document.loaders.document_loader_selector.DocumentLoaderSelector.for_file"
)
LLM_STREAM = "swiss_ai_hub.core.displayers.event_displayer.EventDisplayer.display_llm_stream"
COST_LLM = "swiss_ai_hub.core.generative_ai.resources.models.llm.lite_llm_base.LiteLLMBase.cost_reporting_llm"

ATTACHMENT_FILE_ID = "0d5f7a1c-3b2e-4c8d-9a6f-1e2d3c4b5a6f"
MESSAGE_FILE_ID = "1a2b3c4d-5e6f-4a7b-8c9d-0e1f2a3b4c5d"
SENDER = "alice@test"


def summary(uid: str, subject: str | None = None) -> UnreadMailSummary:
    return UnreadMailSummary(message_id=uid, sender=SENDER, subject=subject or f"Subject {uid}")


def parsed_message(
    message_id: str = "1", subject: str = "Quarterly report", body_text: str = "See attached."
) -> ParsedMessage:
    return ParsedMessage(
        message_id=message_id,
        sender=SENDER,
        subject=subject,
        rfc_message_id=f"<orig-{message_id}@test>",
        body_text=body_text,
        attachments=[ParsedAttachment(filename="report.pdf", content_type="application/pdf", content=b"%PDF-1.4")],
    )


def make_client(
    unread: list[UnreadMailSummary] | None = None,
    undrafted: list[UnreadMailSummary] | None = None,
    folder_created: bool = False,
    created_folders: set[str] | None = None,
) -> AsyncMock:
    """An ImapClient double whose every method matches the real client's signature and return shape.

    ``folder_created`` drives the single-message ``move_message`` path. ``created_folders`` drives the batch
    ``ensure_folders`` path; when it is not given, ``folder_created`` decides whether every requested folder counts
    as newly created, so a scenario only has to state the intent once.
    """

    def ensure_folders(folders: list[str]) -> set[str]:
        if created_folders is not None:
            return created_folders
        return set(folders) if folder_created else set()

    client = AsyncMock()
    client.list_unread = AsyncMock(return_value=unread or [])
    client.move_message = AsyncMock(return_value=folder_created)
    client.relocate_message = AsyncMock(return_value=None)
    client.ensure_folders = AsyncMock(side_effect=ensure_folders)
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


def fake_cost_reporting_llm_yielding(llm: AsyncMock):
    """A ``cost_reporting_llm`` replacement that hands out a caller-supplied LLM double.

    Lets a test configure ``astructured_predict`` and exercise the real prompting code, rather than patching the
    caller of the LLM and skipping the logic under test.
    """

    @asynccontextmanager
    async def _yield_llm(*_args, **_kwargs) -> AsyncIterator[AsyncMock]:
        yield llm

    return _yield_llm


def stored_attachment_refs(
    filename: str = "report.pdf",
    content_type: str = "application/pdf",
    size_bytes: int = 8,
) -> list[MailAttachmentRef]:
    """The S3 references a fetch produces. ``size_bytes`` matters to any caller with a size floor — the default is
    deliberately tiny, so a suite exercising attachment reading has to state a realistic size."""
    return [
        MailAttachmentRef(
            filename=filename, content_type=content_type, file_id=ATTACHMENT_FILE_ID, size_bytes=size_bytes
        )
    ]


def stored_message_ref() -> MailMessageRef:
    return MailMessageRef(filename="1.eml", file_id=MESSAGE_FILE_ID, size_bytes=64)


def archived_eml(
    subject: str = "Quarterly report",
    body: str = "See attached.",
    sender: str = SENDER,
    rfc_message_id: str = "<orig-1@test>",
    reply_to: str | None = None,
    references: str | None = None,
) -> bytes:
    """The raw RFC822 bytes a drafting step reads back out of the archive.

    Built as a real MIME message rather than a `ParsedMessage` double, because the threading headers the reply
    depends on are parsed out of exactly these bytes — a double would let a parser regression through.
    """
    message = EmailMessage(policy=default_policy)
    message["From"] = sender
    message["To"] = "shared-mailbox@test"
    message["Subject"] = subject
    message["Message-ID"] = rfc_message_id
    message["Date"] = "Tue, 25 Aug 2026 09:00:00 +0000"
    if reply_to:
        message["Reply-To"] = reply_to
    if references:
        message["References"] = references
    message.set_content(body)
    return message.as_bytes()


def infrastructure_patches(
    client: AsyncMock,
    llm_event: object | None = None,
    llm: AsyncMock | None = None,
    archived: bytes | None = None,
    load_attachment: AsyncMock | None = None,
    attachment_refs: list[MailAttachmentRef] | None = None,
    llm_stream: AsyncMock | None = None,
) -> tuple:
    """The IMAP factory, the mail store (archive write and read-back), and the LLM, all patched.

    ``llm_event`` is what a patched ``display_llm_stream`` returns; pass the shape the calling suite expects.
    ``llm`` is the double ``cost_reporting_llm`` hands out — pass one to drive real prompting code.
    ``archived`` is the raw message ``load_message`` hands back, which is what a blueprint drafting *after* filing
    reads instead of re-fetching a UID that no longer exists.
    ``load_attachment`` lets a suite assert which attachments were actually fetched — the size floor is only
    observable as a call that never happened.
    ``llm_stream`` lets a suite own the ``display_llm_stream`` double, so it can inspect the prompt after the patches
    have been torn down; without it the mock is created here and unreachable from an assertion.
    """
    cost_llm = fake_cost_reporting_llm_yielding(llm) if llm is not None else fake_cost_reporting_llm
    return (
        patch(FACTORY, side_effect=lambda config: fake_create(client, config)),
        patch(
            STORE_ATTACHMENTS,
            new=AsyncMock(return_value=attachment_refs if attachment_refs is not None else stored_attachment_refs()),
        ),
        patch(STORE_MESSAGE, new=AsyncMock(return_value=stored_message_ref())),
        patch(LOAD_MESSAGE, new=AsyncMock(return_value=archived if archived is not None else archived_eml())),
        patch(LOAD_ATTACHMENT, new=load_attachment or AsyncMock(return_value=b"%PDF-1.4 invoice total 42.00")),
        patch(COST_LLM, new=cost_llm),
        patch(LLM_STREAM, new=llm_stream or AsyncMock(return_value=llm_event)),
    )
