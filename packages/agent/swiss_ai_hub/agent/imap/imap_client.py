import asyncio
import email
import re
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress
from email.message import EmailMessage
from email.policy import default as default_policy

from imapclient import IMAPClient
from imapclient.exceptions import IMAPClientError
from swiss_ai_hub.core.events.agent import UnreadMailSummary
from swiss_ai_hub.core.imap import ImapClientConfig

from swiss_ai_hub.agent.imap.mail_parser import MailParser
from swiss_ai_hub.agent.imap.parsed_message import ParsedMessage

_FLAGS_KEY = b"FLAGS"
_HEADER_KEY = b"BODY[HEADER]"
_BODY_KEY = b"BODY[]"
_SIZE_KEY = b"RFC822.SIZE"
_MOVE_CAPABILITY = b"MOVE"
_UIDPLUS_CAPABILITY = b"UIDPLUS"
_DRAFT_FLAG = b"\\Draft"
_DRAFTS_SPECIAL_USE = b"\\Drafts"
_PERMANENT_FLAGS_KEY = b"PERMANENTFLAGS"
_CUSTOM_KEYWORDS_WILDCARD = b"\\*"
_DRAFTED_KEYWORD = "$AiHubDrafted"
_ANSWERED_FLAG = "\\Answered"


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
        max_message_bytes: int,
    ) -> None:
        self._connection = connection
        self._inbox_folder = inbox_folder
        self._max_messages = max_messages
        self._max_body_bytes = max_body_bytes
        self._max_attachment_bytes = max_attachment_bytes
        self._max_message_bytes = max_message_bytes

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

    async def list_undrafted(self, folder: str, limit: int) -> tuple[str, list[UnreadMailSummary]]:
        """List up to ``limit`` not-yet-drafted messages in ``folder``, and the dedup flag used to identify them.

        The dedup flag is resolved from the same read-only ``SELECT`` used for the search: a custom keyword
        (``$AiHubDrafted``) when the folder's ``PERMANENTFLAGS`` advertises ``\\*``, else ``\\Answered`` — the custom
        keyword is preferred so mail with only an unsent draft is not painted with the standard "replied" indicator.
        The flag is returned so the caller passes the exact value back to ``mark_drafted`` (no stringly-typed guessing).
        ``BODY.PEEK`` keeps every candidate unread.
        """
        response = await asyncio.to_thread(self._connection.select_folder, folder, readonly=True)
        supports_keywords = _CUSTOM_KEYWORDS_WILDCARD in response.get(_PERMANENT_FLAGS_KEY, ())
        drafted_flag = _DRAFTED_KEYWORD if supports_keywords else _ANSWERED_FLAG
        criteria = ["UNKEYWORD", drafted_flag] if supports_keywords else ["UNANSWERED"]
        uids = await asyncio.to_thread(self._connection.search, criteria)

        summaries: list[UnreadMailSummary] = []
        for uid in uids[:limit]:
            fetched = await asyncio.to_thread(self._connection.fetch, [uid], ["BODY.PEEK[HEADER]", "FLAGS"])
            data = fetched[uid]
            message = self._parse_bytes(data[_HEADER_KEY])
            flags = [flag.decode(errors="replace") for flag in data.get(_FLAGS_KEY, ())]
            summaries.append(MailParser.parse_summary(str(uid), message, flags))
        return drafted_flag, summaries

    async def mark_drafted(self, folder: str, message_id: str, drafted_flag: str) -> None:
        """Flag a message as drafted (writable ``SELECT`` + ``STORE``) without setting ``\\Seen`` — it stays unread."""
        await asyncio.to_thread(self._connection.select_folder, folder, readonly=False)
        await asyncio.to_thread(self._connection.add_flags, [int(message_id)], [drafted_flag])

    async def fetch_message(self, message_id: str, folder: str | None = None) -> ParsedMessage:
        """Fetch a single message by UID from ``folder`` (defaults to the inbox), including body and attachments,
        without setting the Seen flag.

        The raw size is checked (a cheap ``RFC822.SIZE`` fetch) before the body is downloaded, so an
        oversized message is refused rather than pulled into memory — this is what bounds peak fetch memory.
        """
        source_folder = folder or self._inbox_folder
        await asyncio.to_thread(self._connection.select_folder, source_folder, readonly=True)
        uid = int(message_id)

        sized = await asyncio.to_thread(self._connection.fetch, [uid], ["RFC822.SIZE"])
        if uid not in sized:
            raise ValueError(f"message {message_id} not found in {source_folder} — it may have been expunged")
        size = sized[uid].get(_SIZE_KEY, 0)
        if size > self._max_message_bytes:
            raise ValueError(
                f"message {message_id} is {size} bytes, exceeding the {self._max_message_bytes}-byte fetch ceiling"
            )

        fetched = await asyncio.to_thread(self._connection.fetch, [uid], ["BODY.PEEK[]"])
        message = self._parse_bytes(fetched[uid][_BODY_KEY])
        return MailParser.parse_message(message_id, message, self._max_body_bytes, self._max_attachment_bytes)

    async def move_message(self, message_id: str, target_folder: str) -> bool:
        """Move a message by UID from the inbox folder into target_folder, opening the folder writable.

        Creates the target folder when it does not exist yet, and reports whether it did — a classifying agent
        files into one folder per category, so the folders cannot be pre-created by hand. Creation runs before
        the inbox is even selected, so a server that refuses it aborts the move with the message still in the
        inbox rather than half-filed.

        Uses the atomic IMAP ``MOVE`` (RFC 6851) when the server supports it; otherwise falls back to
        ``COPY`` + ``UID EXPUNGE`` (RFC 4315, UIDPLUS), which purges only this UID. A server offering neither
        is refused rather than expunged with a blind ``EXPUNGE`` that would also destroy other clients'
        ``\\Deleted`` mail.
        """
        target_folder, folder_created = await self._resolve_or_create_folder(target_folder)
        await asyncio.to_thread(self._connection.select_folder, self._inbox_folder, readonly=False)
        uid = int(message_id)

        present = await asyncio.to_thread(self._connection.fetch, [uid], ["FLAGS"])
        if uid not in present:
            raise ValueError(f"message {message_id} not found in {self._inbox_folder} — it may have been expunged")

        if await asyncio.to_thread(self._connection.has_capability, _MOVE_CAPABILITY):
            await asyncio.to_thread(self._connection.move, [uid], target_folder)
            return folder_created

        if not await asyncio.to_thread(self._connection.has_capability, _UIDPLUS_CAPABILITY):
            raise ValueError(
                f"IMAP server supports neither MOVE nor UIDPLUS — cannot move message {message_id} without risking "
                "other clients' deleted mail"
            )

        await asyncio.to_thread(self._connection.copy, [uid], target_folder)
        await asyncio.to_thread(self._connection.delete_messages, [uid])
        await asyncio.to_thread(self._connection.uid_expunge, [uid])
        return folder_created

    async def append_draft(self, drafts_folder: str, raw_message: bytes) -> tuple[str, str | None]:
        """Append a reply as a ``\\Draft``-flagged message to the drafts folder; never sends (no SMTP path exists).

        The configured name is only trusted when the server's own ``LIST`` returns it verbatim; otherwise the folder
        flagged ``\\Drafts`` (RFC 6154 SPECIAL-USE) is used. This is required because folder names are the server's
        bytes — localized Gmail drafts (e.g. ``[Gmail]/Thư nháp``) and NFC/NFD Unicode differences make a hand-typed
        name mismatch and fail with ``[TRYCREATE]``. Returns the resolved folder and the ``APPENDUID`` (UIDPLUS,
        RFC 4315) when reported.
        """
        target = await self._resolve_folder(drafts_folder, _DRAFTS_SPECIAL_USE)
        response = await asyncio.to_thread(self._connection.append, target, raw_message, flags=[_DRAFT_FLAG])
        return target, self._parse_appenduid(response)

    async def _resolve_folder(self, configured: str, special_use_flag: bytes) -> str:
        """Return the server's exact folder name: the configured one if it exists verbatim, else the special-use match.

        Never trust a retyped name — folder names are the server's bytes (mUTF-7), so a visually-identical config value
        can differ (localization, NFC vs NFD) and select a non-existent folder.
        """
        folders = await asyncio.to_thread(self._connection.list_folders)
        names = {name for _flags, _delim, name in folders}
        if configured and configured in names:
            return configured

        for flags, _delim, name in folders:
            if special_use_flag in flags:
                return name

        available = ", ".join(sorted(names))
        raise ValueError(
            f"folder {configured!r} does not exist on the server and no {special_use_flag!r} special-use folder was "
            f"found. Available folders: {available}"
        )

    async def _resolve_or_create_folder(self, configured: str) -> tuple[str, bool]:
        """Return the target folder name and whether it had to be created — no special-use fallback applies here.

        Each level of the hierarchy is created separately (``Invoices`` before ``Invoices/2026``) because RFC 3501 only
        *recommends* that a server create superior names on its own. Creation failures are not raised directly: a
        parent that already exists fails the same way as a genuinely refused create, and a concurrent run may have won
        the race, so the ``LIST`` afterwards is the sole authority on whether the folder is now there.
        """
        folders = await asyncio.to_thread(self._connection.list_folders)
        if configured in {name for _flags, _delim, name in folders}:
            return configured, False

        delimiter = next((delim.decode() for _flags, delim, _name in folders if delim), None)
        creation_error: IMAPClientError | None = None
        for path in self._hierarchy_paths(configured, delimiter):
            try:
                await asyncio.to_thread(self._connection.create_folder, path)
            except IMAPClientError as error:
                creation_error = error

        created = await asyncio.to_thread(self._connection.list_folders)
        if configured not in {name for _flags, _delim, name in created}:
            raise ValueError(
                f"folder {configured!r} does not exist on the server and could not be created: {creation_error}. "
                f"The message was left in {self._inbox_folder}."
            )

        # A folder nobody is subscribed to stays invisible in most mail clients — the filed mail would look lost.
        with suppress(Exception):
            await asyncio.to_thread(self._connection.subscribe_folder, configured)
        return configured, True

    @staticmethod
    def _hierarchy_paths(folder: str, delimiter: str | None) -> list[str]:
        """Expand a folder name into itself preceded by each of its ancestors; a flat namespace yields just itself."""
        if not delimiter:
            return [folder]
        segments = folder.split(delimiter)
        return [delimiter.join(segments[:depth]) for depth in range(1, len(segments) + 1)]

    @staticmethod
    def _parse_appenduid(response: bytes | str | None) -> str | None:
        if response is None:
            return None
        text = response.decode(errors="replace") if isinstance(response, bytes) else response
        match = re.search(r"APPENDUID\s+\d+\s+(\d+)", text, re.IGNORECASE)
        return match.group(1) if match else None

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
                config.max_message_bytes,
            )
        finally:
            # Best-effort cleanup — a failed logout must never mask the original step failure.
            with suppress(Exception):
                await asyncio.to_thread(connection.logout)
