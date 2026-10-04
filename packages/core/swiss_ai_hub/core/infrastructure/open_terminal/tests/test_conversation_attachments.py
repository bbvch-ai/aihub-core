"""A conversation's attached files land in its folder once, whoever places them, and never over another file."""

import json
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from swiss_ai_hub.core.infrastructure.open_terminal.conversation_attachments import ConversationAttachments
from swiss_ai_hub.core.infrastructure.open_terminal.open_terminal_error import OpenTerminalError

pytestmark = pytest.mark.unit

THREAD = "65f1c0ffee00000000000001"
FOLDER = f"conversations/{THREAD}"


def _client(present: list[str], placed: dict[str, str] | None) -> Any:
    client = MagicMock()
    missing = OpenTerminalError("404: File not found", 404)
    client.view = AsyncMock(
        side_effect=missing if placed is None else None, return_value=(json.dumps(placed).encode(), "text/plain")
    )
    client.list_files = AsyncMock(return_value={"entries": [{"name": name} for name in present]})
    client.upload = AsyncMock(return_value={})
    client.write_file = AsyncMock(return_value={})
    return client


async def _read(file_id: str, filename: str) -> bytes:
    return f"{file_id}:{filename}".encode()


@pytest.mark.asyncio
async def test_a_new_file_is_placed_and_recorded() -> None:
    client = _client(present=[], placed=None)

    where = await ConversationAttachments(client, THREAD).place({"f1": "sales.csv"}, _read)

    client.upload.assert_awaited_once_with(FOLDER, "sales.csv", b"f1:sales.csv")
    client.write_file.assert_awaited_once_with(f"{FOLDER}/.attached_files.json", json.dumps({"f1": "sales.csv"}))
    assert where == {"f1": f"{FOLDER}/sales.csv"}


@pytest.mark.asyncio
async def test_a_placed_file_is_not_placed_again_even_once_deleted() -> None:
    client = _client(present=[], placed={"f1": "sales.csv"})

    where = await ConversationAttachments(client, THREAD).place({"f1": "sales.csv"}, _read)

    client.upload.assert_not_awaited()
    client.write_file.assert_not_awaited()
    assert where == {"f1": f"{FOLDER}/sales.csv"}


@pytest.mark.asyncio
async def test_a_file_whose_name_is_taken_is_placed_beside_the_other() -> None:
    client = _client(present=["sales.csv"], placed={"f1": "sales.csv"})

    await ConversationAttachments(client, THREAD).place({"f1": "sales.csv", "f2": "sales.csv"}, _read)

    client.upload.assert_awaited_once_with(FOLDER, "sales (2).csv", b"f2:sales.csv")


@pytest.mark.asyncio
async def test_nothing_to_place_touches_nothing() -> None:
    client = _client(present=[], placed=None)

    assert await ConversationAttachments(client, THREAD).place({}, _read) == {}
    client.view.assert_not_awaited()


@pytest.mark.asyncio
async def test_a_sandbox_failure_is_not_taken_for_an_empty_folder() -> None:
    client = _client(present=[], placed=None)
    client.view = AsyncMock(side_effect=OpenTerminalError("The code sandbox did not respond", 502))
    attachments = ConversationAttachments(client, THREAD)

    with pytest.raises(OpenTerminalError):
        await attachments.place({"f1": "sales.csv"}, _read)
    client.upload.assert_not_awaited()
