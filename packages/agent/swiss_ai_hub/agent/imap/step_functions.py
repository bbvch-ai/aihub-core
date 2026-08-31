"""Mailbox step bodies shared by every IMAP-backed blueprint.

Free ``do_*`` functions rather than a service class, matching ``rag/step_functions.py`` and
``self_awareness/self_awareness_step_functions.py``: the ``@step`` wrapper owns the event, these own the mailbox work.
They return plain data so a caller can wrap the result in whichever event its own protocol defines — ``ImapAgent``
emits one event per message, a classifying agent summarises a whole batch.
"""

import logging

from swiss_ai_hub.core.events.agent import DraftedReplyRef, MailClassificationRef, UnreadMailSummary
from swiss_ai_hub.core.imap import ImapClientConfig

from swiss_ai_hub.agent.imap.composed_reply import ComposedReply
from swiss_ai_hub.agent.imap.fetched_mail import FetchedMail
from swiss_ai_hub.agent.imap.imap_client import ImapClientFactory
from swiss_ai_hub.agent.imap.mail_store import MailStore
from swiss_ai_hub.agent.imap.message_vanished_error import MessageVanishedError

logger = logging.getLogger(__name__)


async def do_list_unread(imap_config: ImapClientConfig) -> list[UnreadMailSummary]:
    """Open the inbox and return header summaries of the unread messages, oldest sent first."""
    logger.info(
        "[imap] do_list_unread: connecting to %s as %s, folder=%s",
        imap_config.host,
        imap_config.username,
        imap_config.inbox_folder,
    )
    async with ImapClientFactory.create(imap_config) as client:
        summaries = await client.list_unread()
    logger.info("[imap] do_list_unread: found %d unread message(s): %s", len(summaries), [s.subject for s in summaries])
    return summaries


async def do_fetch_and_archive(
    imap_config: ImapClientConfig,
    message_ids: list[str],
    agent_class: str,
    agent_id: str,
    skip_vanished: bool = False,
) -> list[FetchedMail]:
    """Fetch each message with its attachments and archive both the attachments and the original to S3.

    Archiving lives here rather than in a caller so #1575 holds for every blueprint that reads a mailbox — the raw
    bytes are retained only under ``with_raw=True``, which is why the fetch and the archive cannot be separated
    without handing the raw bytes to someone who does not need them.

    Each message is archived and stripped before the next is fetched, so peak memory is one message rather than the
    whole batch: ``max_message_bytes`` bounds a single message, not a run of ``max_messages`` of them. The returned
    ``parsed`` therefore carries no ``raw`` and no attachment bytes — everything downstream reads the S3 references
    instead, and a batch caller holds the list alive across slow LLM round-trips.

    That interleaving keeps the connection open across the S3 writes. Those are in-cluster ``put_object`` calls,
    orders of magnitude below the idle timeout RFC 3501 requires servers to allow; it is the *caller's* LLM work
    that must never span this connection, and it still does not.

    ``skip_vanished`` opts into dropping a UID that disappeared between the listing and the fetch, mirroring
    ``_fetch_summaries``: on a shared mailbox a human filing a message by hand mid-run is routine, and it must cost
    that one message rather than the whole batch. It stays opt-in because a caller fetching a single message has no
    batch to salvage and needs the failure. Only the vanished case is skipped — an oversized message still fails the
    run, because silently skipping it would leave it unread and unreported forever.
    """
    if not message_ids:
        return []

    fetched: list[FetchedMail] = []
    async with ImapClientFactory.create(imap_config) as client:
        for message_id in message_ids:
            try:
                parsed = await client.fetch_message(message_id, with_raw=True)
            except MessageVanishedError:
                if not skip_vanished:
                    raise
                logger.info(
                    "[imap] do_fetch_and_archive: uid=%s vanished before the fetch — skipping it, not the batch",
                    message_id,
                )
                continue

            logger.info(
                "[imap] do_fetch_and_archive: fetched uid=%s from=%s subject=%r date=%s attachments=%d body_len=%d",
                parsed.message_id,
                parsed.sender,
                parsed.subject,
                parsed.date,
                len(parsed.attachments),
                len(parsed.body_text or ""),
            )
            attachments = await MailStore.store_attachments(
                parsed.attachments,
                agent_class=agent_class,
                agent_id=agent_id,
            )
            original_message = await MailStore.store_message(
                parsed.raw,
                message_id=parsed.message_id,
                agent_class=agent_class,
                agent_id=agent_id,
            )
            fetched.append(
                FetchedMail(
                    parsed=parsed.model_copy(update={"raw": b"", "attachments": []}),
                    attachments=attachments,
                    original_message=original_message,
                )
            )
    return fetched


async def do_file_messages(
    imap_config: ImapClientConfig,
    assignments: list[tuple[str, str]],
) -> set[str]:
    """File a whole batch on one connection: ensure every target folder exists, then move each message.

    ``assignments`` pairs a message id with the folder it belongs in; the returned set names the folders that had to
    be created. Filing per message via ``do_file_message`` would open a connection and run a folder ``LIST`` for each
    one — fifty messages cost fifty of both, which servers that cap concurrent or per-interval connections (Gmail
    among them) refuse outright rather than merely slow down.

    Folder creation happening up front also changes the failure mode for the better: a folder the server refuses
    aborts the batch before anything has moved. Filing itself stays sequential, so a mid-batch failure still leaves
    the already-filed messages filed and the rest unread for the next run.
    """
    if not assignments:
        return set()

    target_folders = sorted({folder for _message_id, folder in assignments})
    logger.info(
        "[imap] do_file_messages: filing %d message(s) from %s into %s",
        len(assignments),
        imap_config.inbox_folder,
        target_folders,
    )
    async with ImapClientFactory.create(imap_config) as client:
        created = await client.ensure_folders(target_folders)
        if created:
            logger.info("[imap] do_file_messages: created folder(s) %s", sorted(created))
        for message_id, target_folder in assignments:
            await client.relocate_message(message_id, target_folder)
            logger.info("[imap] do_file_messages: moved uid=%s -> %s", message_id, target_folder)
    return created


async def do_draft_replies(
    imap_config: ImapClientConfig,
    drafts_folder: str,
    replies: list[tuple[MailClassificationRef, ComposedReply]],
) -> list[DraftedReplyRef]:
    """Append a batch of composed replies to the drafts folder on one connection, and never send any of them.

    One connection for the batch, opened only once every model call is done: a socket left idle across a slow LLM
    round-trip gets dropped, and reconnecting per message is what servers capping concurrent connections (Gmail
    included) refuse outright.

    No source message is flagged. The blueprint that calls this has already filed each message out of the inbox, so
    filing is the dedup, and the UID the flag would target died with the ``MOVE``. That is also what makes a partial
    batch safe: the appended drafts stay, and nothing about the filed mail changed.

    A failure aborts the batch rather than the run's earlier work — the mail is filed either way, so the worst case
    is a message whose draft appears on the next run.
    """
    if not replies:
        return []

    logger.info("[imap] do_draft_replies: appending %d draft(s) to %r", len(replies), drafts_folder)
    drafted: list[DraftedReplyRef] = []
    async with ImapClientFactory.create(imap_config) as client:
        for classification, reply in replies:
            resolved_folder, draft_uid = await client.append_draft(drafts_folder, reply.raw)
            logger.info(
                "[imap] do_draft_replies: drafted a reply to uid=%s (%s) -> %r draft_uid=%s",
                classification.message_id,
                classification.category,
                resolved_folder,
                draft_uid,
            )
            drafted.append(
                DraftedReplyRef(
                    source_uid=classification.message_id,
                    category=classification.category,
                    drafts_folder=resolved_folder,
                    draft_uid=draft_uid,
                    in_reply_to=reply.in_reply_to,
                    subject=reply.subject,
                    recipient=reply.recipient,
                )
            )
    return drafted


async def do_file_message(imap_config: ImapClientConfig, message_id: str, target_folder: str) -> bool:
    """Move one message out of the inbox into ``target_folder``, reporting whether the folder had to be created.

    The folder is created when missing (#1636), so a caller filing into per-category folders nobody made by hand
    still succeeds on its first run against a fresh mailbox. Use ``do_file_messages`` for a batch — this opens its
    own connection and lists folders, which is only worth it for a single message.
    """
    logger.info(
        "[imap] do_file_message: moving uid=%s from %s to %s", message_id, imap_config.inbox_folder, target_folder
    )
    async with ImapClientFactory.create(imap_config) as client:
        folder_created = await client.move_message(message_id, target_folder)
    logger.info(
        "[imap] do_file_message: moved uid=%s -> %s folder_created=%s", message_id, target_folder, folder_created
    )
    return folder_created
