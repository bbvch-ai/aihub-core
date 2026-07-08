import asyncio
import email
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress
from email.message import EmailMessage
from email.policy import default as default_policy

from imapclient import IMAPClient
from swiss_ai_hub.core.events.agent import UnreadMailSummary
from swiss_ai_hub.core.imap import ImapClientConfig

from swiss_ai_hub.agent.imap.mail_parser import MailParser
from swiss_ai_hub.agent.imap.parsed_message import ParsedMessage

_FLAGS_KEY = b"FLAGS"
_HEADER_KEY = b"BODY[HEADER]"
_BODY_KEY = b"BODY[]"


class ImapClient:
    """High-level IMAP reader over imapclient — returns parsed domain objects, not raw protocol lines.

    imapclient is synchronous and parses server responses into structured dicts, so every round-trip is
    off-loaded with ``asyncio.to_thread`` to keep the agent event loop free. A client is used sequentially
    within a single step, so the underlying connection is never shared across concurrent tasks.
    """

    def __init__(
        self,
        connection: IMAPClient,
        inbox_folder: str,
        max_messages: int,
        max_body_bytes: int,
        max_attachment_bytes: int,
    ) -> None:
        self._connection = connection
        self._inbox_folder = inbox_folder
        self._max_messages = max_messages
        self._max_body_bytes = max_body_bytes
        self._max_attachment_bytes = max_attachment_bytes

    async def list_unread(self) -> list[UnreadMailSummary]:
        """List unread messages as header summaries, identified by UID so ids stay valid across connections."""
        await asyncio.to_thread(self._connection.select_folder, self._inbox_folder, readonly=True)
        uids = await asyncio.to_thread(self._connection.search, ["UNSEEN"])

        summaries: list[UnreadMailSummary] = []
        for uid in uids[: self._max_messages]:
            fetched = await asyncio.to_thread(self._connection.fetch, [uid], ["BODY.PEEK[HEADER]", "FLAGS"])
            data = fetched[uid]
            message = self._parse_bytes(data[_HEADER_KEY])
            flags = [flag.decode(errors="replace") for flag in data.get(_FLAGS_KEY, ())]
            summaries.append(MailParser.parse_summary(str(uid), message, flags))
        return summaries

    async def fetch_message(self, message_id: str) -> ParsedMessage:
        """Fetch a single message by UID, including body and attachments, without setting the Seen flag."""
        await asyncio.to_thread(self._connection.select_folder, self._inbox_folder, readonly=True)
        uid = int(message_id)
        fetched = await asyncio.to_thread(self._connection.fetch, [uid], ["BODY.PEEK[]"])
        message = self._parse_bytes(fetched[uid][_BODY_KEY])
        return MailParser.parse_message(message_id, message, self._max_body_bytes, self._max_attachment_bytes)

    @staticmethod
    def _parse_bytes(raw: bytes) -> EmailMessage:
        return email.message_from_bytes(raw, policy=default_policy)


class ImapClientFactory:
    """Creates connected ImapClients from ImapClientConfig — used inside agent steps for per-step lifecycle."""

    @staticmethod
    @asynccontextmanager
    async def create(config: ImapClientConfig) -> AsyncIterator[ImapClient]:
        """Connect and log in to the IMAP server, yielding a reader for use within an async with block.

        A read-only SELECT (EXAMINE) plus ``BODY.PEEK[...]`` fetches guarantee the ``\\Seen`` flag is never
        set; imapclient raises on NO/BAD responses, so a failed login or select fails fast instead of
        silently surfacing as an empty inbox.
        """
        connection = await asyncio.to_thread(IMAPClient, config.host, port=config.port, ssl=config.use_tls)
        try:
            await asyncio.to_thread(connection.login, config.username, config.password)
            yield ImapClient(
                connection,
                config.inbox_folder,
                config.max_messages,
                config.max_body_bytes,
                config.max_attachment_bytes,
            )
        finally:
            # Best-effort cleanup — a failed logout must never mask the original step failure.
            with suppress(Exception):
                await asyncio.to_thread(connection.logout)
