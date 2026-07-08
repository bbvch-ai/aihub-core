from unittest.mock import MagicMock, patch

import pytest
from imapclient.exceptions import IMAPClientError, LoginError
from swiss_ai_hub.core.imap import ImapClientConfig
from swiss_ai_hub.core.testing import async_test

from swiss_ai_hub.agent.imap.imap_client import ImapClient, ImapClientFactory

_HEADER = b"From: Alice <alice@example.com>\r\nSubject: Report\r\nDate: Mon, 05 Jan 2026 10:00:00 +0000\r\n\r\n"


def _connection(search: list[int] | None = None, fetch: dict | None = None) -> MagicMock:
    connection = MagicMock()
    connection.search = MagicMock(return_value=[101, 102] if search is None else search)
    if fetch is not None:
        connection.fetch = MagicMock(return_value=fetch)
    else:
        connection.fetch = MagicMock(
            side_effect=lambda uids, _items: {uids[0]: {b"BODY[HEADER]": _HEADER, b"FLAGS": (b"\\Recent",)}}
        )
    return connection


def _client(connection: MagicMock, max_messages: int = 50) -> ImapClient:
    return ImapClient(
        connection,
        inbox_folder="INBOX",
        max_messages=max_messages,
        max_body_bytes=1_000_000,
        max_attachment_bytes=10_000_000,
    )


@async_test
async def test_list_unread_returns_uid_identified_summaries():
    client = _client(_connection())

    summaries = await client.list_unread()

    assert [summary.message_id for summary in summaries] == ["101", "102"]
    assert summaries[0].sender == "Alice <alice@example.com>"
    assert summaries[0].flags == ["\\Recent"]


@async_test
async def test_list_unread_respects_max_messages():
    connection = _connection()
    client = _client(connection, max_messages=1)

    summaries = await client.list_unread()

    assert len(summaries) == 1
    assert connection.fetch.call_count == 1


@async_test
async def test_list_unread_returns_empty_for_empty_inbox():
    client = _client(_connection(search=[]))

    assert await client.list_unread() == []


@async_test
async def test_list_unread_raises_on_failed_select():
    connection = _connection()
    connection.select_folder = MagicMock(side_effect=IMAPClientError("[NONEXISTENT] Unknown Mailbox"))
    client = _client(connection)

    with pytest.raises(IMAPClientError):
        await client.list_unread()


@async_test
async def test_fetch_message_uses_readonly_select_and_peek():
    body = b"From: alice@example.com\r\nSubject: Report\r\n\r\nhello"
    connection = _connection(fetch={101: {b"BODY[]": body}})
    client = _client(connection)

    parsed = await client.fetch_message("101")

    assert parsed.message_id == "101"
    assert parsed.body_text is not None
    assert "hello" in parsed.body_text
    connection.select_folder.assert_called_once_with("INBOX", readonly=True)
    connection.fetch.assert_called_once_with([101], ["BODY.PEEK[]"])


@async_test
async def test_factory_raises_and_logs_out_on_failed_login():
    connection = MagicMock()
    connection.login = MagicMock(side_effect=LoginError("[AUTHENTICATIONFAILED] Invalid credentials"))
    config = ImapClientConfig(host="imap.test", username="a@test", password="wrong")

    with patch("swiss_ai_hub.agent.imap.imap_client.IMAPClient", return_value=connection):
        with pytest.raises(LoginError):
            async with ImapClientFactory.create(config):
                pytest.fail("client must not be yielded after a failed login")

    connection.logout.assert_called_once()
