import asyncio
import email
import logging
import re
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress
from datetime import datetime
from email.message import EmailMessage
from email.policy import default as default_policy
from typing import Any

from imapclient import IMAPClient
from imapclient.exceptions import IMAPClientError
from swiss_ai_hub.core.events.agent import UnreadMailSummary
from swiss_ai_hub.core.imap import ImapClientConfig

from swiss_ai_hub.agent.imap.mail_parser import MailParser
from swiss_ai_hub.agent.imap.message_vanished_error import MessageVanishedError
from swiss_ai_hub.agent.imap.parsed_message import ParsedMessage

logger = logging.getLogger(__name__)

_FLAGS_KEY = b"FLAGS"
_HEADER_KEY = b"BODY[HEADER]"
_BODY_KEY = b"BODY[]"
_SIZE_KEY = b"RFC822.SIZE"
_ENVELOPE_KEY = b"ENVELOPE"
_INTERNALDATE_KEY = b"INTERNALDATE"
_MOVE_CAPABILITY = b"MOVE"
_UIDPLUS_CAPABILITY = b"UIDPLUS"
_SORT_CAPABILITY = b"SORT"
_SENT_DATE_SORT = ("DATE",)
_MAX_ORDERING_CANDIDATES = 1000
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
        self._resolved_source_folder: str | None = None

    async def list_unread(self) -> list[UnreadMailSummary]:
        """List the oldest unread messages as header summaries, identified by UID so ids stay valid across connections.

        Capped at ``max_messages``, oldest sent first — see ``_search_oldest_first`` for why ordering cannot be left to
        the server's ``SEARCH`` order.
        """
        await self._select_source_folder(self._inbox_folder, readonly=True)
        uids = await self._search_oldest_first(["UNSEEN"], self._max_messages)
        return await self._fetch_summaries(uids)

    async def list_undrafted(self, folder: str, limit: int) -> tuple[str, list[UnreadMailSummary]]:
        """List the ``limit`` oldest not-yet-drafted messages in ``folder``, with the dedup flag identifying them.

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
        uids = await self._search_oldest_first(criteria, limit)
        return drafted_flag, await self._fetch_summaries(uids)

    async def _search_oldest_first(self, criteria: list[str], limit: int) -> list[int]:
        """Search the selected folder and return at most ``limit`` UIDs, oldest sent date first.

        Ordering must be explicit: RFC 3501 does not guarantee ``SEARCH`` result order, and the de-facto UID order is
        arrival into *this* folder — a moved message gets a fresh, higher UID, so in the processed folder UID order is
        move order, not send order. Truncation happens after the sort, never before.

        The sort key is the sent date with an ``INTERNALDATE`` fallback, matching RFC 5256 ``SORT DATE`` so the
        server-side and client-side paths agree. ``ARRIVAL`` would not — it ignores the sent date, and would disagree
        with the fallback on exactly the moved-mail case above.

        The server-side branch needs no bound: ``SORT`` returns bare integers the server has already ordered, so
        ``limit`` alone is enough. Asking a server to return only part of a ``SORT`` would need RFC 5267
        ``CONTEXT=SEARCH``/``PARTIAL``, which neither Gmail nor GreenMail advertises.

        The client-side branch cannot know which mail is oldest without dating the candidates, so it is bounded instead
        at ``_MAX_ORDERING_CANDIDATES`` by taking the *lowest* UIDs — the oldest arrivals. That bounds both the metadata
        fetch and the command line it is serialized into: imapclient comma-joins every UID without collapsing ranges,
        and servers cap command length (Dovecot's default 64 KB is roughly 9000 UIDs), so an unbounded fetch over a
        large archive fails outright rather than merely running slow.

        The window costs exactness on one shape of folder. Arrival order is only a proxy for sent order, and in a
        *processed* folder UID order is move order — so with more candidates than the window, the true oldest can fall
        outside it and be missed. Below the window the result is exact. The proxy is sound for an inbox, where the
        oldest-sent mail is all but certainly among the oldest-arrived.

        The lowest UIDs are taken by sorting rather than by slicing the response, because RFC 3501 does not guarantee
        ``SEARCH`` result order — slicing it raw would make the window server-dependent.
        """
        if await asyncio.to_thread(self._connection.has_capability, _SORT_CAPABILITY):
            uids = await asyncio.to_thread(self._connection.sort, _SENT_DATE_SORT, criteria)
            return uids[:limit]

        uids = await asyncio.to_thread(self._connection.search, criteria)
        if not uids:
            return []

        candidates = sorted(uids)[:_MAX_ORDERING_CANDIDATES]
        dated = await asyncio.to_thread(self._connection.fetch, candidates, ["INTERNALDATE", "ENVELOPE"])
        return sorted(candidates, key=lambda uid: self._sent_at(dated.get(uid, {}), uid))[:limit]

    @staticmethod
    def _sent_at(data: dict[bytes, Any], uid: int) -> tuple[datetime, int]:
        """Sort key for one message: its sent date, else its arrival, else last — with the UID breaking ties.

        Every candidate date comes from imapclient, whose ``normalise_times`` yields naive datetimes throughout, so
        ``datetime.max`` is a valid sentinel and the comparison never mixes naive with aware values. Do not feed an
        aware datetime into this key without normalising every branch.
        """
        envelope = data.get(_ENVELOPE_KEY)
        sent_date = envelope.date if envelope else None
        return sent_date or data.get(_INTERNALDATE_KEY) or datetime.max, uid

    async def _fetch_summaries(self, uids: list[int]) -> list[UnreadMailSummary]:
        """Fetch header summaries for ``uids`` in a single round trip, preserving the given order.

        The results are indexed by the requested UIDs rather than iterated from the response, so the ordering
        established by ``_search_oldest_first`` survives whatever order the server answers in.

        A UID absent from the response was expunged by another client between the ``SEARCH`` and this ``FETCH`` — it is
        skipped rather than raising, because a message that no longer exists is not a listing candidate. Batching makes
        this matter: one vanished message would otherwise fail the whole listing instead of only itself.
        """
        if not uids:
            return []

        fetched = await asyncio.to_thread(self._connection.fetch, uids, ["BODY.PEEK[HEADER]", "FLAGS"])
        summaries: list[UnreadMailSummary] = []
        for uid in uids:
            data = fetched.get(uid)
            if data is None:
                continue
            message = self._parse_bytes(data[_HEADER_KEY])
            flags = [flag.decode(errors="replace") for flag in data.get(_FLAGS_KEY, ())]
            summaries.append(MailParser.parse_summary(str(uid), message, flags))
        return summaries

    async def mark_drafted(self, folder: str, message_id: str, drafted_flag: str) -> None:
        """Flag a message as drafted (writable ``SELECT`` + ``STORE``) without setting ``\\Seen`` — it stays unread."""
        await asyncio.to_thread(self._connection.select_folder, folder, readonly=False)
        await asyncio.to_thread(self._connection.add_flags, [int(message_id)], [drafted_flag])

    async def fetch_message(self, message_id: str, folder: str | None = None, with_raw: bool = False) -> ParsedMessage:
        """Fetch a single message by UID from ``folder`` (defaults to the inbox), including body and attachments,
        without setting the Seen flag.

        The raw size is checked (a cheap ``RFC822.SIZE`` fetch) before the body is downloaded, so an
        oversized message is refused rather than pulled into memory — this is what bounds peak fetch memory.

        ``with_raw`` decides whether the downloaded bytes are *retained* on the result. Only the archiving
        caller asks for them: a batch caller holding several results alive across LLM round-trips would
        otherwise retain up to ``max_message_bytes`` per message for data it never reads.
        """
        source_folder = folder or self._inbox_folder
        await asyncio.to_thread(self._connection.select_folder, source_folder, readonly=True)
        uid = int(message_id)

        sized = await asyncio.to_thread(self._connection.fetch, [uid], ["RFC822.SIZE"])
        if uid not in sized:
            raise MessageVanishedError(f"message {message_id} not found in {source_folder} — it may have been expunged")
        size = sized[uid].get(_SIZE_KEY, 0)
        if size > self._max_message_bytes:
            raise ValueError(
                f"message {message_id} is {size} bytes, exceeding the {self._max_message_bytes}-byte fetch ceiling"
            )

        fetched = await asyncio.to_thread(self._connection.fetch, [uid], ["BODY.PEEK[]"])
        raw = fetched[uid][_BODY_KEY]
        message = self._parse_bytes(raw)
        return MailParser.parse_message(
            message_id,
            message,
            self._max_body_bytes,
            self._max_attachment_bytes,
            raw=raw if with_raw else b"",
        )

    async def move_message(self, message_id: str, target_folder: str) -> bool:
        """Move a message by UID from the inbox folder into target_folder, opening the folder writable.

        Creates the target folder when it does not exist yet, and reports whether it did — a classifying agent
        files into one folder per category, so the folders cannot be pre-created by hand. Creation runs before
        the inbox is even selected, so a server that refuses it aborts the move with the message still in the
        inbox rather than half-filed.

        Costs one ``LIST`` per call. A caller filing a whole batch should instead call ``ensure_folders`` once and
        then ``relocate_message`` per message.
        """
        target_folder, folder_created = await self._resolve_or_create_folder(target_folder)
        await self.relocate_message(message_id, target_folder)
        return folder_created

    async def relocate_message(self, message_id: str, target_folder: str) -> None:
        """Move a message into a folder already known to exist — no ``LIST``, no creation.

        Split out of ``move_message`` so a batch caller pays for folder resolution once for the whole run rather
        than once per message.
        """
        await self._select_source_folder(self._inbox_folder, readonly=False)
        uid = int(message_id)

        present = await asyncio.to_thread(self._connection.fetch, [uid], ["FLAGS"])
        if uid not in present:
            raise MessageVanishedError(
                f"message {message_id} not found in {self._inbox_folder} — it may have been expunged"
            )

        await self._relocate_uid(uid, target_folder)

    async def _relocate_uid(self, uid: int, target_folder: str) -> None:
        """Relocate one UID out of the already-selected inbox into ``target_folder``.

        Uses the atomic IMAP ``MOVE`` (RFC 6851) when the server supports it; otherwise falls back to
        ``COPY`` + ``UID EXPUNGE`` (RFC 4315, UIDPLUS), which purges only this UID. A server offering neither
        is refused rather than expunged with a blind ``EXPUNGE`` that would also destroy other clients'
        ``\\Deleted`` mail.
        """
        if await asyncio.to_thread(self._connection.has_capability, _MOVE_CAPABILITY):
            await asyncio.to_thread(self._connection.move, [uid], target_folder)
            return

        if not await asyncio.to_thread(self._connection.has_capability, _UIDPLUS_CAPABILITY):
            raise ValueError(
                f"IMAP server supports neither MOVE nor UIDPLUS — cannot move message {uid} without risking "
                "other clients' deleted mail"
            )

        await asyncio.to_thread(self._connection.copy, [uid], target_folder)
        await asyncio.to_thread(self._connection.delete_messages, [uid])
        await asyncio.to_thread(self._connection.uid_expunge, [uid])

    async def append_draft(self, drafts_folder: str, raw_message: bytes) -> tuple[str, str | None]:
        """Append a reply as a ``\\Draft``-flagged message to the drafts folder; never sends (no SMTP path exists).

        The configured name is only trusted when the server's own ``LIST`` returns it verbatim; otherwise the folder
        flagged ``\\Drafts`` (RFC 6154 SPECIAL-USE) is used, and failing that the configured name is created. This is
        required because folder names are the server's bytes — localized Gmail drafts (e.g. ``[Gmail]/Thư nháp``) and
        NFC/NFD Unicode differences make a hand-typed name mismatch and fail with ``[TRYCREATE]``. Returns the
        resolved folder and the ``APPENDUID`` (UIDPLUS, RFC 4315) when reported.
        """
        target = await self._resolve_folder(drafts_folder, _DRAFTS_SPECIAL_USE)
        response = await asyncio.to_thread(self._connection.append, target, raw_message, flags=[_DRAFT_FLAG])
        return target, self._parse_appenduid(response)

    async def _select_source_folder(self, folder: str, readonly: bool) -> None:
        """`SELECT` a folder the admin typed, resolving it to the server's exact bytes first.

        Resolved once per connection and cached: `relocate_message` selects the source folder for every message it
        moves, and re-listing the mailbox each time is the per-message cost `do_file_messages` opens one connection
        to avoid.

        Gmail matches a label case-insensitively on `CREATE` but demands the exact bytes on `SELECT`, so a configured
        `aihub-test-inbox` against a real `AIHub-Test-Inbox` fails with a bare `[NONEXISTENT] Unknown Mailbox` and the
        run dies before it reads a single message. Unlike the drafts folder there is no special-use flag to fall back
        to and nothing may be created — the source folder must already exist — so the resolution is a case-insensitive
        match against `LIST`, and the error names the near-miss instead of leaving the admin to spot the capital.
        """
        if self._resolved_source_folder is None:
            listed = await asyncio.to_thread(self._connection.list_folders)
            names = [name for _flags, _delim, name in listed]
            match = folder if folder in names else next((n for n in names if n.lower() == folder.lower()), None)
            if match is None:
                available = ", ".join(sorted(names))
                raise ValueError(f"the mailbox has no folder {folder!r}. Available folders: {available}")
            if match != folder:
                logger.info("[imap] resolved configured folder %r to the server's name %r", folder, match)
            self._resolved_source_folder = match
        await asyncio.to_thread(self._connection.select_folder, self._resolved_source_folder, readonly=readonly)

    async def _resolve_folder(self, configured: str, special_use_flag: bytes) -> str:
        """Return the server's exact folder name: the configured one if it exists verbatim, else the special-use
        match, else the configured name created on demand.

        The order is what makes this correct on both kinds of server, and it cannot be rearranged. Verbatim first,
        because a name the server already lists is the name the admin meant. Special-use second, because folder names
        are the server's bytes (mUTF-7) and a visually-identical config value can differ through localization or
        NFC/NFD — Gmail's drafts folder is `[Gmail]/Drafts`, listed in the account's own language, and creating a
        `Drafts` label beside it would silently strand every draft where the user does not look.

        Creation last, for the server that has neither: GreenMail starts with only `INBOX` and advertises no
        SPECIAL-USE, so without this the very first drafting run fails outright instead of making the folder it was
        told to use.
        """
        folders = await asyncio.to_thread(self._connection.list_folders)
        names = {name for _flags, _delim, name in folders}
        if configured and configured in names:
            return configured

        for flags, _delim, name in folders:
            if special_use_flag in flags:
                return name

        if not configured:
            available = ", ".join(sorted(names))
            raise ValueError(
                f"no folder was configured and the server lists no {special_use_flag!r} special-use folder. "
                f"Available folders: {available}"
            )

        await self.ensure_folders([configured])
        return configured

    async def _resolve_or_create_folder(self, configured: str) -> tuple[str, bool]:
        """Return the target folder name and whether it had to be created — no special-use fallback applies here."""
        created = await self.ensure_folders([configured])
        return configured, configured in created

    async def ensure_folders(self, folders: list[str]) -> set[str]:
        """Make sure every folder exists, creating the missing ones, and report which ones had to be created.

        Takes the whole set at once so a batch pays two ``LIST`` commands in total rather than one per folder — and,
        via ``do_file_messages``, one per *message*. Creating up front also means a server that refuses a folder
        aborts before any message has moved, instead of half-way through a batch.

        Each level of the hierarchy is created separately (``Invoices`` before ``Invoices/2026``) because RFC 3501 only
        *recommends* that a server create superior names on its own. Creation failures are not raised directly: a
        parent that already exists fails the same way as a genuinely refused create, and a concurrent run may have won
        the race, so the ``LIST`` afterwards is the sole authority on whether the folder is now there.
        """
        listed = await asyncio.to_thread(self._connection.list_folders)
        existing = {name for _flags, _delim, name in listed}
        missing = [folder for folder in folders if folder not in existing]
        if not missing:
            return set()

        delimiter = next((delim.decode() for _flags, delim, _name in listed if delim), None)
        creation_error: IMAPClientError | None = None
        for folder in missing:
            for path in self._hierarchy_paths(folder, delimiter):
                try:
                    await asyncio.to_thread(self._connection.create_folder, path)
                except IMAPClientError as error:
                    creation_error = error

        relisted = await asyncio.to_thread(self._connection.list_folders)
        now_existing = {name for _flags, _delim, name in relisted}
        still_missing = [folder for folder in missing if folder not in now_existing]
        if still_missing:
            reason = creation_error or "the server accepted the creation but does not list the folder"
            raise ValueError(
                f"folder(s) {', '.join(repr(f) for f in still_missing)} do not exist on the server and could not be "
                f"created: {reason}. No message was moved out of {self._inbox_folder}."
            )

        # A folder nobody is subscribed to stays invisible in most mail clients — the filed mail would look lost.
        for folder in missing:
            with suppress(Exception):
                await asyncio.to_thread(self._connection.subscribe_folder, folder)
        return set(missing)

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
