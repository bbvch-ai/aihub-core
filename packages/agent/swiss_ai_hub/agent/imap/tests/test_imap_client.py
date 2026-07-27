from unittest.mock import MagicMock, patch

import pytest
from imapclient.exceptions import IMAPClientError, LoginError
from swiss_ai_hub.core.imap import ImapClientConfig
from swiss_ai_hub.core.testing import async_test

from swiss_ai_hub.agent.imap.imap_client import ImapClient, ImapClientFactory

_HEADER = b"From: Alice <alice@example.com>\r\nSubject: Report\r\nDate: Mon, 05 Jan 2026 10:00:00 +0000\r\n\r\n"


_FOLDERS = [
    ((b"\\HasNoChildren",), b"/", "INBOX"),
    ((b"\\HasNoChildren",), b"/", "Processed"),
    ((b"\\Drafts", b"\\HasNoChildren"), b"/", "[Gmail]/Drafts"),
]


def _connection(search: list[int] | None = None, fetch: dict | None = None, folders: list | None = None) -> MagicMock:
    connection = MagicMock()
    connection.list_folders = MagicMock(return_value=_FOLDERS if folders is None else folders)
    connection.search = MagicMock(return_value=[101, 102] if search is None else search)
    if fetch is not None:
        connection.fetch = MagicMock(return_value=fetch)
    else:
        connection.fetch = MagicMock(
            side_effect=lambda uids, _items: {uids[0]: {b"BODY[HEADER]": _HEADER, b"FLAGS": (b"\\Recent",)}}
        )
    return connection


def _client(connection: MagicMock, max_messages: int = 50, max_message_bytes: int = 50_000_000) -> ImapClient:
    return ImapClient(
        connection,
        inbox_folder="INBOX",
        max_messages=max_messages,
        max_body_bytes=1_000_000,
        max_attachment_bytes=10_000_000,
        max_message_bytes=max_message_bytes,
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
    connection = _connection(fetch={101: {b"RFC822.SIZE": len(body), b"BODY[]": body}})
    client = _client(connection)

    parsed = await client.fetch_message("101")

    assert parsed.message_id == "101"
    assert parsed.body_text is not None
    assert "hello" in parsed.body_text
    connection.select_folder.assert_called_once_with("INBOX", readonly=True)
    fetch_calls = [call.args for call in connection.fetch.call_args_list]
    assert fetch_calls == [([101], ["RFC822.SIZE"]), ([101], ["BODY.PEEK[]"])]


@async_test
async def test_fetch_message_refuses_oversized_message_without_downloading_body():
    connection = _connection(fetch={101: {b"RFC822.SIZE": 500}})
    client = _client(connection, max_message_bytes=100)

    with pytest.raises(ValueError, match="exceeding"):
        await client.fetch_message("101")

    assert connection.fetch.call_count == 1
    assert connection.fetch.call_args.args == ([101], ["RFC822.SIZE"])


@async_test
async def test_fetch_message_raises_on_expunged_uid():
    connection = _connection(fetch={})
    client = _client(connection)

    with pytest.raises(ValueError, match="expunged"):
        await client.fetch_message("101")


@async_test
async def test_fetch_message_reads_from_given_folder():
    body = b"From: alice@example.com\r\nSubject: Report\r\n\r\nhello"
    connection = _connection(fetch={101: {b"RFC822.SIZE": len(body), b"BODY[]": body}})
    client = _client(connection)

    await client.fetch_message("101", folder="Processed")

    connection.select_folder.assert_called_once_with("Processed", readonly=True)


@async_test
async def test_move_message_uses_atomic_move_when_supported():
    connection = _connection(fetch={101: {b"FLAGS": ()}})
    connection.has_capability = MagicMock(return_value=True)
    client = _client(connection)

    await client.move_message("101", "Processed")

    connection.select_folder.assert_called_once_with("INBOX", readonly=False)
    connection.move.assert_called_once_with([101], "Processed")
    connection.copy.assert_not_called()


@async_test
async def test_move_message_falls_back_to_copy_and_uid_expunge_without_move():
    connection = _connection(fetch={101: {b"FLAGS": ()}})
    connection.has_capability = MagicMock(side_effect=lambda capability: capability == b"UIDPLUS")
    client = _client(connection)

    await client.move_message("101", "Processed")

    connection.move.assert_not_called()
    connection.copy.assert_called_once_with([101], "Processed")
    connection.delete_messages.assert_called_once_with([101])
    connection.uid_expunge.assert_called_once_with([101])


@async_test
async def test_move_message_refuses_when_neither_move_nor_uidplus():
    connection = _connection(fetch={101: {b"FLAGS": ()}})
    connection.has_capability = MagicMock(return_value=False)
    client = _client(connection)

    with pytest.raises(ValueError, match="neither MOVE nor UIDPLUS"):
        await client.move_message("101", "Processed")

    connection.copy.assert_not_called()


@async_test
async def test_move_message_raises_actionable_error_when_target_folder_missing():
    connection = _connection(fetch={101: {b"FLAGS": ()}})
    connection.has_capability = MagicMock(return_value=True)
    client = _client(connection)

    with pytest.raises(ValueError, match="does not exist"):
        await client.move_message("101", "DoesNotExist")

    connection.move.assert_not_called()


@async_test
async def test_move_message_raises_on_expunged_uid_without_mutating():
    connection = _connection(fetch={})
    connection.has_capability = MagicMock(return_value=True)
    client = _client(connection)

    with pytest.raises(ValueError, match="expunged"):
        await client.move_message("101", "Processed")

    connection.move.assert_not_called()


@async_test
async def test_append_draft_uses_configured_folder_when_it_exists_verbatim():
    connection = _connection()
    connection.append = MagicMock(return_value=b"[APPENDUID 130 57] (Success)")
    client = _client(connection)

    resolved, uid = await client.append_draft("Processed", b"From: me\r\nSubject: Re: Hi\r\n\r\nBody")

    assert (resolved, uid) == ("Processed", "57")
    _folder, _msg = connection.append.call_args.args
    assert _folder == "Processed"
    assert connection.append.call_args.kwargs["flags"] == [b"\\Draft"]


@async_test
async def test_append_draft_auto_resolves_drafts_special_use_when_name_mismatches():
    connection = _connection()
    connection.append = MagicMock(return_value=b"[APPENDUID 130 57] (Success)")
    client = _client(connection)

    resolved, uid = await client.append_draft("Drafts", b"raw")

    assert resolved == "[Gmail]/Drafts"
    assert uid == "57"
    assert connection.append.call_args.args[0] == "[Gmail]/Drafts"


@async_test
async def test_append_draft_auto_resolves_when_folder_left_blank():
    connection = _connection()
    connection.append = MagicMock(return_value=b"[APPENDUID 130 57] (Success)")
    client = _client(connection)

    resolved, _uid = await client.append_draft("", b"raw")

    assert resolved == "[Gmail]/Drafts"


@async_test
async def test_append_draft_raises_actionable_error_when_no_drafts_folder():
    connection = _connection(folders=[((b"\\HasNoChildren",), b"/", "INBOX")])
    connection.append = MagicMock(return_value=b"[APPENDUID 130 57] (Success)")
    client = _client(connection)

    with pytest.raises(ValueError, match="Available folders: INBOX"):
        await client.append_draft("", b"raw")

    connection.append.assert_not_called()


@async_test
async def test_append_draft_returns_none_without_uidplus():
    connection = _connection()
    connection.append = MagicMock(return_value=b"(Success)")
    client = _client(connection)

    _resolved, uid = await client.append_draft("Processed", b"raw")
    assert uid is None


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


@async_test
async def test_list_undrafted_uses_unkeyword_and_returns_custom_keyword_when_supported():
    connection = _connection(search=[11, 12])
    connection.select_folder = MagicMock(return_value={b"PERMANENTFLAGS": (b"\\Seen", b"\\*")})
    client = _client(connection)

    drafted_flag, summaries = await client.list_undrafted("Processed", limit=5)

    assert drafted_flag == "$AiHubDrafted"
    assert [s.message_id for s in summaries] == ["11", "12"]
    connection.select_folder.assert_called_once_with("Processed", readonly=True)
    assert connection.search.call_args.args[0] == ["UNKEYWORD", "$AiHubDrafted"]


@async_test
async def test_list_undrafted_falls_back_to_unanswered_without_keyword_support_and_caps_at_limit():
    connection = _connection(search=[11, 12, 13])
    connection.select_folder = MagicMock(return_value={b"PERMANENTFLAGS": (b"\\Seen", b"\\Answered")})
    client = _client(connection)

    drafted_flag, summaries = await client.list_undrafted("Processed", limit=2)

    assert drafted_flag == "\\Answered"
    assert len(summaries) == 2
    assert connection.search.call_args.args[0] == ["UNANSWERED"]


@async_test
async def test_mark_drafted_adds_flag_writable_without_seen():
    connection = _connection()
    client = _client(connection)

    await client.mark_drafted("Processed", "11", "$AiHubDrafted")

    connection.select_folder.assert_called_once_with("Processed", readonly=False)
    connection.add_flags.assert_called_once_with([11], ["$AiHubDrafted"])
