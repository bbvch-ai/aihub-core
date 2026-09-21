from contextlib import ExitStack
from unittest.mock import AsyncMock, patch

import pytest
from swiss_ai_hub.core.imap import ImapClientConfig
from swiss_ai_hub.core.testing import async_test

from swiss_ai_hub.agent.imap.message_vanished_error import MessageVanishedError
from swiss_ai_hub.agent.imap.step_functions import (
    do_fetch_and_archive,
    do_file_message,
    do_file_messages,
    do_list_unread,
)
from swiss_ai_hub.agent.imap.tests.mail_doubles import (
    FACTORY,
    STORE_ATTACHMENTS,
    STORE_MESSAGE,
    fake_create,
    make_client,
    parsed_message,
    stored_attachment_refs,
    stored_message_ref,
    summary,
)

_AGENT_CLASS = "EmailClassificationAgent"
_AGENT_ID = "mailbox"


def _config() -> ImapClientConfig:
    return ImapClientConfig(host="imap.test", username="a@test", password="secret")


def _store_patches(client: AsyncMock) -> tuple:
    return (
        patch(FACTORY, side_effect=lambda config: fake_create(client, config)),
        patch(STORE_ATTACHMENTS, new=AsyncMock(return_value=stored_attachment_refs())),
        patch(STORE_MESSAGE, new=AsyncMock(return_value=stored_message_ref())),
    )


@async_test
async def test_list_unread_returns_the_clients_summaries_in_order():
    client = make_client(unread=[summary("3"), summary("7")])

    with patch(FACTORY, side_effect=lambda config: fake_create(client, config)):
        summaries = await do_list_unread(_config())

    assert [s.message_id for s in summaries] == ["3", "7"]


@async_test
async def test_fetch_and_archive_stores_attachments_and_the_original_for_every_message():
    """#1575 lives here now, so both blueprints archive identically — a batch stores one original per message."""
    client = make_client()
    client.fetch_message = AsyncMock(side_effect=lambda message_id, **_: parsed_message(message_id=message_id))
    store_attachments = AsyncMock(return_value=stored_attachment_refs())
    store_message = AsyncMock(return_value=stored_message_ref())

    with (
        patch(FACTORY, side_effect=lambda config: fake_create(client, config)),
        patch(STORE_ATTACHMENTS, new=store_attachments),
        patch(STORE_MESSAGE, new=store_message),
    ):
        fetched = await do_fetch_and_archive(_config(), ["11", "12"], _AGENT_CLASS, _AGENT_ID)

    assert [f.parsed.message_id for f in fetched] == ["11", "12"]
    assert store_attachments.await_count == 2
    assert store_message.await_count == 2
    assert all(f.original_message is not None for f in fetched)
    assert all(f.attachments[0].filename == "report.pdf" for f in fetched)


@async_test
async def test_fetch_and_archive_always_retains_the_raw_bytes():
    """``with_raw=True`` is what makes archiving possible; a caller must never be able to lose it by omission."""
    client = make_client()

    with ExitStack() as stack:
        for patcher in _store_patches(client):
            stack.enter_context(patcher)
        await do_fetch_and_archive(_config(), ["1"], _AGENT_CLASS, _AGENT_ID)

    assert client.fetch_message.await_args.kwargs["with_raw"] is True


@async_test
async def test_fetch_and_archive_returns_no_raw_or_attachment_bytes():
    """A batch caller holds these across every LLM round-trip, so the bytes must not survive the archive.

    ``max_message_bytes`` bounds one message, not a run of ``max_messages`` of them — retaining the batch would put
    the ceiling at the product of the two, for fields nothing downstream reads once the S3 refs exist.
    """
    client = make_client()
    client.fetch_message = AsyncMock(side_effect=lambda message_id, **_: parsed_message(message_id=message_id))

    with ExitStack() as stack:
        for patcher in _store_patches(client):
            stack.enter_context(patcher)
        fetched = await do_fetch_and_archive(_config(), ["11", "12"], _AGENT_CLASS, _AGENT_ID)

    assert all(f.parsed.raw == b"" for f in fetched)
    assert all(f.parsed.attachments == [] for f in fetched)
    assert all(f.attachments[0].filename == "report.pdf" for f in fetched)
    assert all(f.parsed.subject for f in fetched)


@async_test
async def test_fetch_and_archive_archives_each_message_before_fetching_the_next():
    """Interleaving is what keeps peak memory at one message instead of the whole batch."""
    client = make_client()
    order: list[str] = []
    client.fetch_message = AsyncMock(
        side_effect=lambda message_id, **_: (order.append(f"fetch {message_id}"), parsed_message(message_id))[1]
    )
    store_message = AsyncMock(
        side_effect=lambda *_a, **kwargs: (order.append(f"store {kwargs['message_id']}"), None)[1]
    )

    with (
        patch(FACTORY, side_effect=lambda config: fake_create(client, config)),
        patch(STORE_ATTACHMENTS, new=AsyncMock(return_value=[])),
        patch(STORE_MESSAGE, new=store_message),
    ):
        await do_fetch_and_archive(_config(), ["11", "12"], _AGENT_CLASS, _AGENT_ID)

    assert order == ["fetch 11", "store 11", "fetch 12", "store 12"]


@async_test
async def test_a_vanished_message_is_skipped_rather_than_failing_the_batch():
    """A human filing a message by hand mid-run is routine on a shared mailbox — it must cost that message only."""
    client = make_client()
    client.fetch_message = AsyncMock(
        side_effect=[parsed_message("11"), MessageVanishedError("uid 12 was expunged"), parsed_message("13")]
    )

    with ExitStack() as stack:
        for patcher in _store_patches(client):
            stack.enter_context(patcher)
        fetched = await do_fetch_and_archive(_config(), ["11", "12", "13"], _AGENT_CLASS, _AGENT_ID, skip_vanished=True)

    assert [f.parsed.message_id for f in fetched] == ["11", "13"]


@async_test
async def test_a_vanished_message_fails_the_fetch_unless_skipping_was_asked_for():
    """``ImapAgent`` fetches one message and needs the failure — it has no batch to salvage."""
    client = make_client()
    client.fetch_message = AsyncMock(side_effect=MessageVanishedError("uid 11 was expunged"))

    with ExitStack() as stack:
        for patcher in _store_patches(client):
            stack.enter_context(patcher)
        with pytest.raises(MessageVanishedError):
            await do_fetch_and_archive(_config(), ["11"], _AGENT_CLASS, _AGENT_ID)


@async_test
async def test_an_oversized_message_still_fails_even_when_vanished_ones_are_skipped():
    """The skip must stay narrow: a message refused by max_message_bytes is a real failure, not a race.

    Both are raised as ValueError, so catching that broadly would leave an oversized message unread and unreported
    on every run instead of once, loudly.
    """
    client = make_client()
    client.fetch_message = AsyncMock(side_effect=ValueError("message 11 is 99 bytes, exceeding the 10-byte ceiling"))

    with ExitStack() as stack:
        for patcher in _store_patches(client):
            stack.enter_context(patcher)
        with pytest.raises(ValueError, match="exceeding"):
            await do_fetch_and_archive(_config(), ["11"], _AGENT_CLASS, _AGENT_ID, skip_vanished=True)


@async_test
async def test_fetch_and_archive_of_nothing_touches_no_connection():
    client = make_client()

    with patch(FACTORY, side_effect=lambda config: fake_create(client, config)) as factory:
        assert await do_fetch_and_archive(_config(), [], _AGENT_CLASS, _AGENT_ID) == []

    assert factory.call_count == 0


@async_test
async def test_file_message_reports_whether_the_folder_had_to_be_created():
    client = make_client(folder_created=True)

    with patch(FACTORY, side_effect=lambda config: fake_create(client, config)):
        created = await do_file_message(_config(), "42", "Invoices/2026")

    assert created is True
    client.move_message.assert_awaited_once_with("42", "Invoices/2026")


@async_test
async def test_file_message_reports_no_creation_for_an_existing_folder():
    client = make_client(folder_created=False)

    with patch(FACTORY, side_effect=lambda config: fake_create(client, config)):
        assert await do_file_message(_config(), "42", "Invoices") is False


@async_test
async def test_filing_a_batch_uses_one_connection_and_one_folder_check():
    """The point of the batch path: fifty messages must not cost fifty connections and fifty folder listings."""
    client = make_client()
    assignments = [("1", "Triage/Support"), ("2", "Triage/Invoices"), ("3", "Triage/Support")]

    with patch(FACTORY, side_effect=lambda config: fake_create(client, config)) as factory:
        await do_file_messages(_config(), assignments)

    assert factory.call_count == 1
    client.ensure_folders.assert_awaited_once_with(["Triage/Invoices", "Triage/Support"])
    assert client.relocate_message.await_count == 3


@async_test
async def test_filing_a_batch_moves_every_message_to_its_own_folder():
    client = make_client()
    assignments = [("1", "Triage/Support"), ("2", "Triage/Invoices")]

    with patch(FACTORY, side_effect=lambda config: fake_create(client, config)):
        await do_file_messages(_config(), assignments)

    assert [call.args for call in client.relocate_message.await_args_list] == assignments


@async_test
async def test_filing_a_batch_reports_the_folders_it_created():
    client = make_client(created_folders={"Triage/Support"})

    with patch(FACTORY, side_effect=lambda config: fake_create(client, config)):
        created = await do_file_messages(_config(), [("1", "Triage/Support"), ("2", "Triage/Invoices")])

    assert created == {"Triage/Support"}


@async_test
async def test_filing_an_empty_batch_touches_no_connection():
    client = make_client()

    with patch(FACTORY, side_effect=lambda config: fake_create(client, config)) as factory:
        assert await do_file_messages(_config(), []) == set()

    assert factory.call_count == 0


@async_test
async def test_a_failed_move_leaves_the_rest_of_the_batch_unfiled():
    """Filing is sequential on purpose: the messages already moved stay moved, the rest stay unread for next run."""
    client = make_client()
    client.relocate_message = AsyncMock(side_effect=[None, ValueError("uid 2 was expunged")])

    imap_config = _config()

    with patch(FACTORY, side_effect=lambda config: fake_create(client, config)):
        with pytest.raises(ValueError, match="expunged"):
            await do_file_messages(imap_config, [("1", "A"), ("2", "A"), ("3", "A")])

    assert client.relocate_message.await_count == 2
