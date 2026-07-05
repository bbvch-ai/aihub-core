from unittest.mock import AsyncMock, patch

import pytest
from aioimaplib import Response
from swiss_ai_hub.core.imap import ImapClientConfig
from swiss_ai_hub.core.testing import async_test

from swiss_ai_hub.agent.imap.imap_client import ImapClient, ImapClientFactory
from swiss_ai_hub.agent.imap.imap_command_error import ImapCommandError

_HEADER = b"From: Alice <alice@example.com>\r\nSubject: Report\r\nDate: Mon, 05 Jan 2026 10:00:00 +0000\r\n\r\n"


def _fetch_response(payload: bytes, item: bytes) -> Response:
    return Response(
        "OK",
        [
            b"1 FETCH (UID 101 FLAGS (\\Recent) " + item + b" {%d}" % len(payload),
            bytearray(payload),
            b")",
        ],
    )


def _connection(
    select: Response | None = None,
    uid_search: Response | None = None,
    uid: Response | None = None,
) -> AsyncMock:
    connection = AsyncMock()
    connection.select = AsyncMock(return_value=select or Response("OK", [b"2 EXISTS"]))
    connection.uid_search = AsyncMock(
        return_value=uid_search or Response("OK", [b"101 102", b"UID SEARCH completed"])
    )
    connection.uid = AsyncMock(return_value=uid or _fetch_response(_HEADER, b"BODY[HEADER]"))
    return connection


@async_test
async def test_list_unread_returns_uid_identified_summaries():
    client = ImapClient(_connection(), inbox_folder="INBOX", max_messages=50)

    summaries = await client.list_unread()

    assert [summary.message_id for summary in summaries] == ["101", "102"]
    assert summaries[0].sender == "Alice <alice@example.com>"
    assert summaries[0].flags == ["\\Recent"]


@async_test
async def test_list_unread_respects_max_messages():
    connection = _connection()
    client = ImapClient(connection, inbox_folder="INBOX", max_messages=1)

    summaries = await client.list_unread()

    assert len(summaries) == 1
    assert connection.uid.await_count == 1


@async_test
async def test_list_unread_returns_empty_for_empty_inbox():
    connection = _connection(uid_search=Response("OK", [b"", b"UID SEARCH completed"]))
    client = ImapClient(connection, inbox_folder="INBOX", max_messages=50)

    assert await client.list_unread() == []


@async_test
async def test_list_unread_raises_on_failed_select():
    connection = _connection(select=Response("NO", [b"[NONEXISTENT] Unknown Mailbox"]))
    client = ImapClient(connection, inbox_folder="INBOX", max_messages=50)

    with pytest.raises(ImapCommandError, match="SELECT"):
        await client.list_unread()


@async_test
async def test_fetch_message_uses_uid_fetch_with_peek():
    body = b"From: alice@example.com\r\nSubject: Report\r\n\r\nhello"
    connection = _connection(uid=_fetch_response(body, b"BODY[]"))
    client = ImapClient(connection, inbox_folder="INBOX", max_messages=50)

    parsed = await client.fetch_message("101")

    assert parsed.message_id == "101"
    assert parsed.body_text is not None
    assert "hello" in parsed.body_text
    connection.uid.assert_awaited_once_with("fetch", "101", "(BODY.PEEK[])")


@async_test
async def test_factory_raises_and_logs_out_on_failed_login():
    connection = AsyncMock()
    connection.login = AsyncMock(return_value=Response("NO", [b"[AUTHENTICATIONFAILED] Invalid credentials"]))
    config = ImapClientConfig(host="imap.test", username="a@test", password="wrong")

    with patch("aioimaplib.IMAP4_SSL", return_value=connection):
        with pytest.raises(ImapCommandError, match="LOGIN"):
            async with ImapClientFactory.create(config):
                pytest.fail("client must not be yielded after a failed login")

    connection.logout.assert_awaited_once()
