"""Mailbox step bodies shared by every IMAP-backed blueprint.

Free ``do_*`` functions rather than a service class, matching ``rag/step_functions.py`` and
``self_awareness/self_awareness_step_functions.py``: the ``@step`` wrapper owns the event, these own the mailbox work.
They return plain data so a caller can wrap the result in whichever event its own protocol defines — ``ImapAgent``
emits one event per message, a classifying agent summarises a whole batch.
"""

import logging

from swiss_ai_hub.core.events.agent import UnreadMailSummary
from swiss_ai_hub.core.imap import ImapClientConfig

from swiss_ai_hub.agent.imap.fetched_mail import FetchedMail
from swiss_ai_hub.agent.imap.imap_client import ImapClientFactory
from swiss_ai_hub.agent.imap.mail_store import MailStore

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
) -> list[FetchedMail]:
    """Fetch each message with its attachments and archive both the attachments and the original to S3.

    One short-lived connection covers the whole batch: the socket is closed before the caller does anything slow
    with the results, because many servers drop an idle connection mid-batch.

    Archiving lives here rather than in a caller so #1575 holds for every blueprint that reads a mailbox — the raw
    bytes are retained only under ``with_raw=True``, which is why the fetch and the archive cannot be separated
    without handing the raw bytes to someone who does not need them.
    """
    if not message_ids:
        return []

    async with ImapClientFactory.create(imap_config) as client:
        parsed_messages = [await client.fetch_message(message_id, with_raw=True) for message_id in message_ids]

    fetched: list[FetchedMail] = []
    for parsed in parsed_messages:
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
        fetched.append(FetchedMail(parsed=parsed, attachments=attachments, original_message=original_message))
    return fetched


async def do_file_message(imap_config: ImapClientConfig, message_id: str, target_folder: str) -> bool:
    """Move one message out of the inbox into ``target_folder``, reporting whether the folder had to be created.

    The folder is created when missing (#1636), so a caller filing into per-category folders nobody made by hand
    still succeeds on its first run against a fresh mailbox.
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
