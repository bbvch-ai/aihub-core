import email
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from email.message import EmailMessage
from email.policy import default as default_policy

import aioimaplib
from swiss_ai_hub.core.events.agent import UnreadMailSummary
from swiss_ai_hub.core.imap.imap_client_config import ImapClientConfig

from swiss_ai_hub.agent.imap.mail_parser import MailParser
from swiss_ai_hub.agent.imap.parsed_message import ParsedMessage


class ImapClient:
    """High-level async IMAP reader over aioimaplib — returns parsed domain objects, not raw protocol lines."""

    def __init__(self, connection: aioimaplib.IMAP4, inbox_folder: str) -> None:
        self._connection = connection
        self._inbox_folder = inbox_folder

    async def list_unread(self) -> list[UnreadMailSummary]:
        """List unread messages in the inbox as lightweight header summaries."""
        await self._connection.select(self._inbox_folder)
        search = await self._connection.search("UNSEEN")
        message_ids = search.lines[0].split() if search.lines and search.lines[0] else []

        summaries: list[UnreadMailSummary] = []
        for raw_id in message_ids:
            message_id = raw_id.decode()
            fetched = await self._connection.fetch(message_id, "(FLAGS BODY.PEEK[HEADER])")
            header_bytes = self._extract_literal(fetched.lines)
            message = self._parse_bytes(header_bytes)
            flags = self._extract_flags(fetched.lines)
            summaries.append(MailParser.parse_summary(message_id, message, flags))
        return summaries

    async def fetch_message(self, message_id: str) -> ParsedMessage:
        """Fetch a single message by id, including body and attachments."""
        await self._connection.select(self._inbox_folder)
        fetched = await self._connection.fetch(message_id, "(RFC822)")
        message = self._parse_bytes(self._extract_literal(fetched.lines))
        return MailParser.parse_message(message_id, message)

    @staticmethod
    def _parse_bytes(raw: bytes) -> EmailMessage:
        return email.message_from_bytes(raw, policy=default_policy)

    @staticmethod
    def _extract_literal(lines: list[bytes]) -> bytes:
        """Pick the message literal from an aioimaplib fetch response, skipping protocol metadata lines."""
        candidates = [
            bytes(line)
            for line in lines
            if isinstance(line, bytearray | bytes) and not line.rstrip().endswith(b")")
        ]
        payloads = [line for line in candidates if b"FETCH" not in line[:64]]
        return max(payloads, key=len) if payloads else b""

    @staticmethod
    def _extract_flags(lines: list[bytes]) -> list[str]:
        for line in lines:
            text = bytes(line).decode(errors="replace") if isinstance(line, bytearray | bytes) else str(line)
            start = text.find("FLAGS (")
            if start != -1:
                end = text.find(")", start)
                return text[start + len("FLAGS (") : end].split()
        return []


class ImapClientFactory:
    """Creates connected ImapClients from ImapClientConfig — used inside agent steps for per-step lifecycle."""

    @staticmethod
    @asynccontextmanager
    async def create(config: ImapClientConfig) -> AsyncIterator[ImapClient]:
        """Connect and log in to the IMAP server, yielding a reader for use within an async with block."""
        if config.use_tls:
            connection = aioimaplib.IMAP4_SSL(host=config.host, port=config.port)
        else:
            connection = aioimaplib.IMAP4(host=config.host, port=config.port)

        await connection.wait_hello_from_server()
        await connection.login(config.username, config.password)
        try:
            yield ImapClient(connection, config.inbox_folder)
        finally:
            await connection.logout()
