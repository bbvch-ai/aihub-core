from collections.abc import Callable
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from imapclient.exceptions import IMAPClientError, LoginError
from imapclient.response_types import Envelope
from swiss_ai_hub.core.imap import ImapClientConfig
from swiss_ai_hub.core.testing import async_test

from swiss_ai_hub.agent.imap.imap_client import _MAX_ORDERING_CANDIDATES, ImapClient, ImapClientFactory

_HEADER = b"From: Alice <alice@example.com>\r\nSubject: Report\r\nDate: Mon, 05 Jan 2026 10:00:00 +0000\r\n\r\n"


_FOLDERS = [
    ((b"\\HasNoChildren",), b"/", "INBOX"),
    ((b"\\HasNoChildren",), b"/", "Processed"),
    ((b"\\Drafts", b"\\HasNoChildren"), b"/", "[Gmail]/Drafts"),
]

_KEYWORD_FOLDER = {b"PERMANENTFLAGS": (b"\\Seen", b"\\*")}


def _folders_after_creating(name: str, base: list | None = None) -> Callable[..., list]:
    """LIST answers that only contain ``name`` from the second call on — i.e. once the client has created it."""
    existing = _FOLDERS if base is None else base
    delimiter = next((delim for _flags, delim, _name in existing if delim), None)
    calls: list[int] = []

    def list_folders(*_args) -> list:
        calls.append(1)
        if len(calls) == 1:
            return existing
        return [*existing, ((b"\\HasNoChildren",), delimiter, name)]

    return list_folders


def _envelope(sent_at: datetime | None) -> Envelope:
    """A minimal Envelope carrying only the sent date — naive, exactly as imapclient's normalise_times produces."""
    return Envelope(sent_at, None, None, None, None, None, None, None, None, None)


def _dated(dates: dict[int, datetime | None], internaldates: dict[int, datetime] | None = None) -> dict:
    """FETCH response for the ordering fetch: an ENVELOPE per UID, plus INTERNALDATE where the server reports one."""
    internaldates = internaldates or {}
    return {
        uid: {b"ENVELOPE": _envelope(sent_at)} | ({b"INTERNALDATE": internaldates[uid]} if uid in internaldates else {})
        for uid, sent_at in dates.items()
    }


def _summary_fetch(uids: list[int]) -> dict:
    return {uid: {b"BODY[HEADER]": _HEADER, b"FLAGS": (b"\\Recent",)} for uid in uids}


def _connection(
    search: list[int] | None = None,
    fetch: dict | None = None,
    folders: list | Callable[..., list] | None = None,
    supports_sort: bool = False,
    dated: dict | None = None,
) -> MagicMock:
    """A mocked IMAP connection.

    ``supports_sort`` defaults to False so the client-side ordering path is what the bulk of the suite exercises; a
    bare MagicMock would make ``has_capability`` truthy and silently route every test through the server-side branch.
    """
    connection = MagicMock()
    if callable(folders):
        connection.list_folders = MagicMock(side_effect=folders)
    else:
        connection.list_folders = MagicMock(return_value=_FOLDERS if folders is None else folders)
    connection.search = MagicMock(return_value=[101, 102] if search is None else search)
    connection.has_capability = MagicMock(side_effect=lambda capability: supports_sort and capability == b"SORT")
    connection.sort = MagicMock(return_value=[101, 102] if search is None else search)
    if fetch is not None:
        connection.fetch = MagicMock(return_value=fetch)
    else:
        connection.fetch = MagicMock(
            side_effect=lambda uids, items: dated if dated is not None and "ENVELOPE" in items else _summary_fetch(uids)
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
    assert connection.fetch.call_args.args == ([101], ["BODY.PEEK[HEADER]", "FLAGS"])


@async_test
async def test_list_unread_batches_the_summary_fetch_into_one_round_trip():
    connection = _connection(search=[101, 102, 103])
    client = _client(connection)

    summaries = await client.list_unread()

    assert [s.message_id for s in summaries] == ["101", "102", "103"]
    summary_fetches = [c.args for c in connection.fetch.call_args_list if "FLAGS" in c.args[1]]
    assert summary_fetches == [([101, 102, 103], ["BODY.PEEK[HEADER]", "FLAGS"])]


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
async def test_fetch_message_drops_the_raw_bytes_unless_they_are_asked_for():
    """The batch drafting chain holds several results alive across its LLM calls and never archives, so
    retaining the downloaded bytes there would cost up to max_message_bytes per message for nothing."""
    body = b"From: alice@example.com\r\nSubject: Report\r\n\r\nhello"
    connection = _connection(fetch={101: {b"RFC822.SIZE": len(body), b"BODY[]": body}})
    client = _client(connection)

    assert (await client.fetch_message("101")).raw == b""


@async_test
async def test_fetch_message_retains_the_raw_bytes_for_the_archiving_caller():
    body = b"From: alice@example.com\r\nSubject: Report\r\n\r\nhello"
    connection = _connection(fetch={101: {b"RFC822.SIZE": len(body), b"BODY[]": body}})
    client = _client(connection)

    assert (await client.fetch_message("101", with_raw=True)).raw == body


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
async def test_move_message_leaves_an_existing_target_folder_untouched():
    connection = _connection(fetch={101: {b"FLAGS": ()}})
    connection.has_capability = MagicMock(return_value=True)
    client = _client(connection)

    folder_created = await client.move_message("101", "Processed")

    assert folder_created is False
    connection.create_folder.assert_not_called()
    connection.move.assert_called_once_with([101], "Processed")


@async_test
async def test_move_message_creates_the_target_folder_when_it_does_not_exist():
    connection = _connection(fetch={101: {b"FLAGS": ()}}, folders=_folders_after_creating("Invoices"))
    connection.has_capability = MagicMock(return_value=True)
    client = _client(connection)

    folder_created = await client.move_message("101", "Invoices")

    assert folder_created is True
    connection.create_folder.assert_called_once_with("Invoices")
    connection.subscribe_folder.assert_called_once_with("Invoices")
    connection.move.assert_called_once_with([101], "Invoices")


@async_test
async def test_move_message_creates_each_ancestor_of_a_nested_target_folder():
    connection = _connection(fetch={101: {b"FLAGS": ()}}, folders=_folders_after_creating("Invoices/2026/Q1"))
    connection.has_capability = MagicMock(return_value=True)
    client = _client(connection)

    await client.move_message("101", "Invoices/2026/Q1")

    assert [call.args[0] for call in connection.create_folder.call_args_list] == [
        "Invoices",
        "Invoices/2026",
        "Invoices/2026/Q1",
    ]


@async_test
async def test_move_message_creates_the_full_name_at_once_in_a_flat_namespace():
    flat = [((b"\\HasNoChildren",), None, "INBOX")]
    connection = _connection(fetch={101: {b"FLAGS": ()}}, folders=_folders_after_creating("Invoices.2026", flat))
    connection.has_capability = MagicMock(return_value=True)
    client = _client(connection)

    await client.move_message("101", "Invoices.2026")

    connection.create_folder.assert_called_once_with("Invoices.2026")


@async_test
async def test_move_message_files_the_message_when_a_concurrent_run_created_the_folder_first():
    connection = _connection(fetch={101: {b"FLAGS": ()}}, folders=_folders_after_creating("Invoices"))
    connection.has_capability = MagicMock(return_value=True)
    connection.create_folder = MagicMock(side_effect=IMAPClientError("[ALREADYEXISTS] Mailbox exists"))
    client = _client(connection)

    folder_created = await client.move_message("101", "Invoices")

    assert folder_created is True
    connection.move.assert_called_once_with([101], "Invoices")


@async_test
async def test_move_message_reports_a_refused_creation_without_touching_the_message():
    connection = _connection(fetch={101: {b"FLAGS": ()}})
    connection.has_capability = MagicMock(return_value=True)
    connection.create_folder = MagicMock(side_effect=IMAPClientError("[CANNOT] Permission denied"))
    client = _client(connection)

    with pytest.raises(ValueError, match="could not be created: .*Permission denied"):
        await client.move_message("101", "Invoices")

    connection.move.assert_not_called()
    connection.copy.assert_not_called()
    connection.select_folder.assert_not_called()


@async_test
async def test_move_message_reports_a_creation_the_server_acknowledged_but_did_not_perform():
    connection = _connection(fetch={101: {b"FLAGS": ()}})
    connection.has_capability = MagicMock(return_value=True)
    client = _client(connection)

    with pytest.raises(ValueError, match="accepted the creation but does not list the folder"):
        await client.move_message("101", "Invoices")

    connection.move.assert_not_called()
    connection.select_folder.assert_not_called()


@async_test
async def test_move_message_still_files_when_the_server_refuses_to_subscribe_the_new_folder():
    connection = _connection(fetch={101: {b"FLAGS": ()}}, folders=_folders_after_creating("Invoices"))
    connection.has_capability = MagicMock(return_value=True)
    connection.subscribe_folder = MagicMock(side_effect=IMAPClientError("SUBSCRIBE unsupported"))
    client = _client(connection)

    assert await client.move_message("101", "Invoices") is True
    connection.move.assert_called_once_with([101], "Invoices")


@async_test
async def test_move_message_creates_the_target_folder_on_the_copy_fallback_too():
    connection = _connection(fetch={101: {b"FLAGS": ()}}, folders=_folders_after_creating("Invoices"))
    connection.has_capability = MagicMock(side_effect=lambda capability: capability == b"UIDPLUS")
    client = _client(connection)

    assert await client.move_message("101", "Invoices") is True
    connection.create_folder.assert_called_once_with("Invoices")
    connection.copy.assert_called_once_with([101], "Invoices")


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
async def test_list_undrafted_uses_server_sort_when_supported():
    connection = _connection(search=[11, 12], supports_sort=True)
    connection.select_folder = MagicMock(return_value=_KEYWORD_FOLDER)
    client = _client(connection)

    _flag, summaries = await client.list_undrafted("Processed", limit=5)

    connection.sort.assert_called_once_with(("DATE",), ["UNKEYWORD", "$AiHubDrafted"])
    connection.search.assert_not_called()
    assert [s.message_id for s in summaries] == ["11", "12"]


@async_test
async def test_list_undrafted_returns_server_sort_ids_verbatim():
    connection = _connection(search=[97, 12, 45], supports_sort=True)
    connection.select_folder = MagicMock(return_value=_KEYWORD_FOLDER)
    client = _client(connection)

    _flag, summaries = await client.list_undrafted("Processed", limit=5)

    assert [s.message_id for s in summaries] == ["97", "12", "45"]


@async_test
async def test_list_undrafted_sorts_by_sent_date_when_sort_unsupported():
    connection = _connection(
        search=[13, 11, 12],
        dated=_dated(
            {
                13: datetime(2026, 1, 5, 10, 0),
                11: datetime(2026, 3, 9, 8, 30),
                12: datetime(2026, 2, 1, 12, 0),
            }
        ),
    )
    connection.select_folder = MagicMock(return_value=_KEYWORD_FOLDER)
    client = _client(connection)

    _flag, summaries = await client.list_undrafted("Processed", limit=5)

    assert [s.message_id for s in summaries] == ["13", "12", "11"]


@async_test
async def test_list_undrafted_falls_back_to_internaldate_without_envelope_date():
    connection = _connection(
        search=[11, 12],
        dated=_dated({11: None, 12: datetime(2026, 2, 1, 12, 0)}, internaldates={11: datetime(2026, 1, 1, 9, 0)}),
    )
    connection.select_folder = MagicMock(return_value=_KEYWORD_FOLDER)
    client = _client(connection)

    _flag, summaries = await client.list_undrafted("Processed", limit=5)

    assert [s.message_id for s in summaries] == ["11", "12"]


@async_test
async def test_list_undrafted_places_undatable_messages_last_with_uid_tiebreak():
    connection = _connection(
        search=[30, 20, 11],
        dated=_dated({30: None, 20: None, 11: datetime(2026, 6, 1, 9, 0)}),
    )
    connection.select_folder = MagicMock(return_value=_KEYWORD_FOLDER)
    client = _client(connection)

    _flag, summaries = await client.list_undrafted("Processed", limit=5)

    assert [s.message_id for s in summaries] == ["11", "20", "30"]


@async_test
async def test_list_undrafted_sorts_before_applying_limit():
    connection = _connection(
        search=[11, 12, 13],
        dated=_dated(
            {
                11: datetime(2026, 9, 1, 9, 0),
                12: datetime(2026, 1, 1, 9, 0),
                13: datetime(2026, 2, 1, 9, 0),
            }
        ),
    )
    connection.select_folder = MagicMock(return_value=_KEYWORD_FOLDER)
    client = _client(connection)

    _flag, summaries = await client.list_undrafted("Processed", limit=2)

    assert [s.message_id for s in summaries] == ["12", "13"]


@async_test
async def test_ordering_fetch_is_capped_at_the_candidate_window():
    """The metadata fetch must be bounded: unbounded, it serializes into a command line servers reject outright."""
    matches = list(range(1, _MAX_ORDERING_CANDIDATES + 501))
    connection = _connection(
        search=matches,
        dated=_dated({uid: datetime(2026, 1, 1, 9, 0) for uid in matches}),
    )
    connection.select_folder = MagicMock(return_value=_KEYWORD_FOLDER)
    client = _client(connection)

    await client.list_undrafted("Processed", limit=5)

    ordering_fetch = next(call for call in connection.fetch.call_args_list if "ENVELOPE" in call.args[1])
    assert ordering_fetch.args[0] == matches[:_MAX_ORDERING_CANDIDATES]


@async_test
async def test_ordering_window_takes_the_lowest_uids_not_the_search_response_order():
    """RFC 3501 does not guarantee SEARCH ordering, so the window must not depend on the order the server replied in."""
    matches = list(reversed(range(1, _MAX_ORDERING_CANDIDATES + 501)))
    connection = _connection(
        search=matches,
        dated=_dated({uid: datetime(2026, 1, 1, 9, 0) for uid in matches}),
    )
    connection.select_folder = MagicMock(return_value=_KEYWORD_FOLDER)
    client = _client(connection)

    await client.list_undrafted("Processed", limit=5)

    ordering_fetch = next(call for call in connection.fetch.call_args_list if "ENVELOPE" in call.args[1])
    assert ordering_fetch.args[0] == sorted(matches)[:_MAX_ORDERING_CANDIDATES]


@async_test
async def test_ordering_below_the_window_still_dates_every_candidate():
    """Under the window the result stays exact — the cap must not truncate a folder small enough to date fully."""
    matches = [11, 12, 13]
    connection = _connection(
        search=matches,
        dated=_dated({11: datetime(2026, 9, 1, 9, 0), 12: datetime(2026, 1, 1, 9, 0), 13: datetime(2026, 2, 1, 9, 0)}),
    )
    connection.select_folder = MagicMock(return_value=_KEYWORD_FOLDER)
    client = _client(connection)

    _flag, summaries = await client.list_undrafted("Processed", limit=3)

    ordering_fetch = next(call for call in connection.fetch.call_args_list if "ENVELOPE" in call.args[1])
    assert ordering_fetch.args[0] == matches
    assert [s.message_id for s in summaries] == ["12", "13", "11"]


@async_test
async def test_server_sort_is_not_capped_by_the_candidate_window():
    """SORT returns bare ordered integers, so the window would only discard correct ordering the server already did."""
    ordered = list(range(1, _MAX_ORDERING_CANDIDATES + 501))
    connection = _connection(search=ordered, supports_sort=True)
    connection.select_folder = MagicMock(return_value=_KEYWORD_FOLDER)
    client = _client(connection)

    _flag, summaries = await client.list_undrafted("Processed", limit=3)

    assert [s.message_id for s in summaries] == ["1", "2", "3"]
    assert not [call for call in connection.fetch.call_args_list if "ENVELOPE" in call.args[1]]


@async_test
async def test_list_unread_sorts_before_applying_max_messages():
    connection = _connection(
        search=[101, 102, 103],
        dated=_dated(
            {
                101: datetime(2026, 9, 1, 9, 0),
                102: datetime(2026, 1, 1, 9, 0),
                103: datetime(2026, 2, 1, 9, 0),
            }
        ),
    )
    client = _client(connection, max_messages=2)

    summaries = await client.list_unread()

    assert [s.message_id for s in summaries] == ["102", "103"]


@async_test
@pytest.mark.parametrize("supports_sort", [True, False])
async def test_ordering_never_selects_writable_nor_requests_seen_setting_fetch_items(supports_sort: bool):
    connection = _connection(search=[11, 12], supports_sort=supports_sort, dated=_dated({11: None, 12: None}))
    connection.select_folder = MagicMock(return_value=_KEYWORD_FOLDER)
    client = _client(connection)

    await client.list_undrafted("Processed", limit=5)

    assert all(call.kwargs["readonly"] for call in connection.select_folder.call_args_list)
    requested = [item for call in connection.fetch.call_args_list for item in call.args[1]]
    assert not any(item.startswith("RFC822") or item.startswith("BODY[") for item in requested)


@async_test
async def test_list_undrafted_skips_a_message_expunged_between_search_and_fetch():
    dated = _dated({11: datetime(2026, 1, 1, 9, 0), 12: datetime(2026, 2, 1, 9, 0)})
    connection = _connection(search=[11, 12])
    connection.select_folder = MagicMock(return_value=_KEYWORD_FOLDER)
    connection.fetch = MagicMock(
        side_effect=lambda uids, items: dated if "ENVELOPE" in items else _summary_fetch([u for u in uids if u != 12])
    )
    client = _client(connection)

    _flag, summaries = await client.list_undrafted("Processed", limit=5)

    assert [s.message_id for s in summaries] == ["11"]


@async_test
async def test_list_undrafted_sorts_an_undatable_expunged_message_last():
    connection = _connection(search=[11, 12])
    connection.select_folder = MagicMock(return_value=_KEYWORD_FOLDER)
    connection.fetch = MagicMock(
        side_effect=lambda uids, items: (
            _dated({12: datetime(2026, 2, 1, 9, 0)}) if "ENVELOPE" in items else _summary_fetch(uids)
        )
    )
    client = _client(connection)

    _flag, summaries = await client.list_undrafted("Processed", limit=5)

    assert [s.message_id for s in summaries] == ["12", "11"]


@async_test
async def test_mark_drafted_adds_flag_writable_without_seen():
    connection = _connection()
    client = _client(connection)

    await client.mark_drafted("Processed", "11", "$AiHubDrafted")

    connection.select_folder.assert_called_once_with("Processed", readonly=False)
    connection.add_flags.assert_called_once_with([11], ["$AiHubDrafted"])


# --- ensure_folders: the batch path, where the whole run pays one folder check ---


@async_test
async def test_ensure_folders_lists_once_for_a_whole_batch():
    """One LIST for the batch is the entire point — filing per message cost one LIST per message."""
    connection = _connection()
    client = _client(connection)

    created = await client.ensure_folders(["INBOX", "Processed"])

    assert created == set()
    assert connection.list_folders.call_count == 1
    connection.create_folder.assert_not_called()


@async_test
async def test_ensure_folders_creates_only_the_missing_ones():
    connection = _connection(folders=_folders_after_creating("Invoices"))
    client = _client(connection)

    created = await client.ensure_folders(["Processed", "Invoices"])

    assert created == {"Invoices"}
    connection.create_folder.assert_called_once_with("Invoices")
    connection.subscribe_folder.assert_called_once_with("Invoices")


@async_test
async def test_ensure_folders_creates_every_ancestor_of_each_missing_folder():
    existing = _FOLDERS
    delimiter = b"/"
    listed: list[int] = []

    def list_folders(*_args) -> list:
        listed.append(1)
        if len(listed) == 1:
            return existing
        return [
            *existing,
            ((b"\\HasNoChildren",), delimiter, "Triage/Support"),
            ((b"\\HasNoChildren",), delimiter, "Triage/Invoices"),
        ]

    connection = _connection(folders=list_folders)
    client = _client(connection)

    created = await client.ensure_folders(["Triage/Support", "Triage/Invoices"])

    assert created == {"Triage/Support", "Triage/Invoices"}
    assert [call.args[0] for call in connection.create_folder.call_args_list] == [
        "Triage",
        "Triage/Support",
        "Triage",
        "Triage/Invoices",
    ]
    assert connection.list_folders.call_count == 2


@async_test
async def test_ensure_folders_names_every_folder_it_could_not_create():
    connection = _connection()
    connection.create_folder = MagicMock(side_effect=IMAPClientError("[CANNOT] Permission denied"))
    client = _client(connection)

    with pytest.raises(ValueError, match="'Invoices'.*'Archive'"):
        await client.ensure_folders(["Invoices", "Archive"])


@async_test
async def test_ensure_folders_refuses_before_any_message_moves():
    """Creating up front is what makes a refused folder abort the batch instead of stranding it half-filed."""
    connection = _connection()
    connection.create_folder = MagicMock(side_effect=IMAPClientError("[CANNOT] Permission denied"))
    client = _client(connection)

    with pytest.raises(ValueError, match="No message was moved out of INBOX"):
        await client.ensure_folders(["Invoices"])

    connection.select_folder.assert_not_called()
    connection.move.assert_not_called()


# --- relocate_message: the move with folder resolution already done ---


@async_test
async def test_relocate_message_moves_without_listing_folders():
    connection = _connection(fetch={101: {b"FLAGS": ()}})
    connection.has_capability = MagicMock(return_value=True)
    client = _client(connection)

    await client.relocate_message("101", "Processed")

    connection.list_folders.assert_not_called()
    connection.move.assert_called_once_with([101], "Processed")


@async_test
async def test_relocate_message_refuses_a_uid_that_is_no_longer_in_the_inbox():
    connection = _connection(fetch={})
    connection.has_capability = MagicMock(return_value=True)
    client = _client(connection)

    with pytest.raises(ValueError, match="not found in INBOX"):
        await client.relocate_message("101", "Processed")

    connection.move.assert_not_called()


@async_test
async def test_append_draft_creates_the_configured_folder_when_the_server_has_no_drafts_folder_at_all():
    """The GreenMail shape: only INBOX exists and no SPECIAL-USE is advertised.

    Without this the very first drafting run against a fresh test server fails outright instead of making the folder
    it was told to use.
    """
    # Three LIST calls happen here — the resolve, then ensure_folders either side of the create — so the folder must
    # only appear on the third. `_folders_after_creating` reveals it on the second, which is the different case of a
    # concurrent run having won the race.
    inbox_only = [((b"\\HasNoChildren",), b".", "INBOX")]
    listings = iter([inbox_only, inbox_only, [*inbox_only, ((b"\\HasNoChildren",), b".", "Drafts")]])
    connection = _connection(folders=lambda *_args: next(listings))
    connection.append = MagicMock(return_value=b"[APPENDUID 130 57] (Success)")
    client = _client(connection)

    resolved, uid = await client.append_draft("Drafts", b"raw")

    assert resolved == "Drafts"
    assert uid == "57"
    connection.create_folder.assert_called_once_with("Drafts")


@async_test
async def test_append_draft_prefers_the_special_use_folder_over_creating_the_configured_name():
    """Order matters more than the fallback itself.

    Gmail's real drafts folder is `[Gmail]/Drafts`, listed in the account's own language. Creating a `Drafts` label
    beside it would silently strand every draft where the user never looks.
    """
    connection = _connection(
        folders=[
            ((b"\\HasNoChildren",), b"/", "INBOX"),
            ((b"\\HasNoChildren", b"\\Drafts"), b"/", "[Gmail]/Drafts"),
        ]
    )
    connection.append = MagicMock(return_value=b"(Success)")
    client = _client(connection)

    resolved, _uid = await client.append_draft("Drafts", b"raw")

    assert resolved == "[Gmail]/Drafts"
    connection.create_folder.assert_not_called()


@async_test
async def test_append_draft_reports_a_folder_it_could_not_create():
    """A server that refuses the folder must fail before the append, not append into nothing."""
    connection = _connection(folders=[((b"\\HasNoChildren",), b".", "INBOX")])
    connection.create_folder = MagicMock(side_effect=IMAPClientError("permission denied"))
    connection.append = MagicMock(return_value=b"(Success)")
    client = _client(connection)

    with pytest.raises(ValueError, match="could not be created"):
        await client.append_draft("Drafts", b"raw")

    connection.append.assert_not_called()
