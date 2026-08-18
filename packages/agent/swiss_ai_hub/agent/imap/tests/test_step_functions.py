from contextlib import ExitStack
from unittest.mock import AsyncMock, patch

from swiss_ai_hub.core.imap import ImapClientConfig
from swiss_ai_hub.core.testing import async_test

from swiss_ai_hub.agent.imap.step_functions import do_fetch_and_archive, do_file_message, do_list_unread
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
