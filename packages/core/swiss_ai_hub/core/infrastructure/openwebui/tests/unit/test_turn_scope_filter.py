"""Unit tests for the OpenWebUI inlet filter ``aihub_turn_scope_filter``.

The filter lives under ``infra/`` as an OpenWebUI function, outside any Python package, so it is loaded from its
file path with the ``open_webui`` runtime stubbed. The generated copy is the one the stack registers; the template is
the one people edit — the drift test keeps them equal, which ``make generate-compose`` otherwise guarantees.
"""

import importlib.util
import sys
import types
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock

import pytest

pytestmark = pytest.mark.unit

REPO_ROOT = Path(__file__).resolve().parents[8]
GENERATED_FILTER = REPO_ROOT / "infra/configs/openwebui/functions/aihub_turn_scope_filter.py"
TEMPLATE_FILTER = REPO_ROOT / "infra/deployment/templates/openwebui_functions/aihub_turn_scope_filter.py"

OLD_FILE = {"type": "file", "id": "old-1", "name": "earlier.pdf"}
NEW_FILE_A = {"type": "file", "id": "new-a", "name": "now-a.pdf"}
NEW_FILE_B = {"type": "file", "id": "new-b", "name": "now-b.pdf"}
COLLECTION = {"type": "collection", "id": "kb-1", "name": "Handbook"}
AGENT_MODEL = {"id": "aihub-agent-RAGAgent-hr"}
PLAIN_MODEL = {"id": "aihub-model-text-generation-gemma"}


@pytest.fixture
def chats_stub(monkeypatch: pytest.MonkeyPatch) -> AsyncMock:
    chats = AsyncMock()
    chats_module = types.ModuleType("open_webui.models.chats")
    chats_module.Chats = chats
    monkeypatch.setitem(sys.modules, "open_webui", types.ModuleType("open_webui"))
    monkeypatch.setitem(sys.modules, "open_webui.models", types.ModuleType("open_webui.models"))
    monkeypatch.setitem(sys.modules, "open_webui.models.chats", chats_module)
    return chats


@pytest.fixture
def turn_scope_filter(chats_stub: AsyncMock) -> Any:
    spec = importlib.util.spec_from_file_location("aihub_turn_scope_filter", GENERATED_FILTER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.Filter()


def _body(*files: dict[str, Any]) -> dict[str, Any]:
    return {"model": "irrelevant", "messages": [{"role": "user", "content": "summarise this"}], "files": list(files)}


def _metadata(current_turn_files: list[dict[str, Any]] | None, **extra: Any) -> dict[str, Any]:
    metadata: dict[str, Any] = {"chat_id": "chat-1", "message_id": "assistant-2", **extra}
    if current_turn_files is not None:
        metadata["user_message"] = {"id": "user-2", "role": "user", "files": current_turn_files}
    return metadata


def test_generated_copy_matches_template():
    assert GENERATED_FILTER.read_text(encoding="utf-8") == TEMPLATE_FILTER.read_text(encoding="utf-8")


def test_header_description_has_no_apostrophe():
    """``init-openwebui.sh`` embeds the description in a single-quoted SQL literal."""
    header = GENERATED_FILTER.read_text(encoding="utf-8").split('"""')[1]
    assert "'" not in header


@pytest.mark.asyncio
async def test_should_keep_only_current_turn_files_when_turn_attaches_files(turn_scope_filter):
    body = _body(OLD_FILE, NEW_FILE_A)

    result = await turn_scope_filter.inlet(body, __metadata__=_metadata([NEW_FILE_A]), __model__=AGENT_MODEL)

    assert result["files"] == [NEW_FILE_A]


@pytest.mark.asyncio
async def test_should_keep_every_file_of_the_turn_when_several_are_attached(turn_scope_filter):
    body = _body(OLD_FILE, NEW_FILE_A, NEW_FILE_B)

    result = await turn_scope_filter.inlet(
        body, __metadata__=_metadata([NEW_FILE_A, NEW_FILE_B]), __model__=AGENT_MODEL
    )

    assert result["files"] == [NEW_FILE_A, NEW_FILE_B]


@pytest.mark.asyncio
async def test_should_keep_whole_conversation_when_turn_attaches_nothing(turn_scope_filter):
    body = _body(OLD_FILE, NEW_FILE_A)

    result = await turn_scope_filter.inlet(body, __metadata__=_metadata([]), __model__=AGENT_MODEL)

    assert result["files"] == [OLD_FILE, NEW_FILE_A]


@pytest.mark.asyncio
async def test_should_leave_non_file_items_in_place(turn_scope_filter):
    body = _body(COLLECTION, OLD_FILE, NEW_FILE_A)

    result = await turn_scope_filter.inlet(body, __metadata__=_metadata([NEW_FILE_A]), __model__=AGENT_MODEL)

    assert result["files"] == [COLLECTION, NEW_FILE_A]


@pytest.mark.asyncio
async def test_should_ignore_non_file_attachments_when_deciding_the_turn(turn_scope_filter):
    """A turn that attaches only a collection did not attach a file, so earlier files stay."""
    body = _body(OLD_FILE, COLLECTION)

    result = await turn_scope_filter.inlet(body, __metadata__=_metadata([COLLECTION]), __model__=AGENT_MODEL)

    assert result["files"] == [OLD_FILE, COLLECTION]


@pytest.mark.asyncio
async def test_should_not_touch_plain_models_by_default(turn_scope_filter):
    body = _body(OLD_FILE, NEW_FILE_A)

    result = await turn_scope_filter.inlet(body, __metadata__=_metadata([NEW_FILE_A]), __model__=PLAIN_MODEL)

    assert result["files"] == [OLD_FILE, NEW_FILE_A]


@pytest.mark.asyncio
async def test_should_scope_plain_models_when_valve_disables_agent_only(turn_scope_filter):
    turn_scope_filter.valves.agent_models_only = False
    body = _body(OLD_FILE, NEW_FILE_A)

    result = await turn_scope_filter.inlet(body, __metadata__=_metadata([NEW_FILE_A]), __model__=PLAIN_MODEL)

    assert result["files"] == [NEW_FILE_A]


@pytest.mark.asyncio
async def test_should_return_body_unchanged_when_no_files(turn_scope_filter, chats_stub):
    body = _body()

    result = await turn_scope_filter.inlet(body, __metadata__=_metadata([NEW_FILE_A]), __model__=AGENT_MODEL)

    assert result == body
    chats_stub.get_message_by_id_and_message_id.assert_not_awaited()


@pytest.mark.asyncio
async def test_should_fall_back_to_stored_user_message_by_id(turn_scope_filter, chats_stub):
    chats_stub.get_message_by_id_and_message_id.return_value = {"id": "user-2", "files": [NEW_FILE_A]}
    body = _body(OLD_FILE, NEW_FILE_A)

    result = await turn_scope_filter.inlet(
        body, __metadata__=_metadata(None, user_message_id="user-2"), __model__=AGENT_MODEL
    )

    assert result["files"] == [NEW_FILE_A]
    chats_stub.get_message_by_id_and_message_id.assert_awaited_once_with("chat-1", "user-2")


@pytest.mark.asyncio
async def test_should_fall_back_through_the_assistant_message_parent(turn_scope_filter, chats_stub):
    chats_stub.get_message_by_id_and_message_id.side_effect = [
        {"id": "assistant-2", "parentId": "user-2"},
        {"id": "user-2", "files": [NEW_FILE_A]},
    ]
    body = _body(OLD_FILE, NEW_FILE_A)

    result = await turn_scope_filter.inlet(body, __metadata__=_metadata(None), __model__=AGENT_MODEL)

    assert result["files"] == [NEW_FILE_A]
    assert [call.args for call in chats_stub.get_message_by_id_and_message_id.await_args_list] == [
        ("chat-1", "assistant-2"),
        ("chat-1", "user-2"),
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize("chat_id", ["local:temp", "channel:general", None])
async def test_should_leave_unpersisted_chats_untouched_without_user_message(turn_scope_filter, chats_stub, chat_id):
    body = _body(OLD_FILE, NEW_FILE_A)

    result = await turn_scope_filter.inlet(
        body, __metadata__={"chat_id": chat_id, "message_id": "assistant-2"}, __model__=AGENT_MODEL
    )

    assert result["files"] == [OLD_FILE, NEW_FILE_A]
    chats_stub.get_message_by_id_and_message_id.assert_not_awaited()


@pytest.mark.asyncio
async def test_should_leave_files_untouched_when_stored_message_is_missing(turn_scope_filter, chats_stub):
    chats_stub.get_message_by_id_and_message_id.return_value = None
    body = _body(OLD_FILE, NEW_FILE_A)

    result = await turn_scope_filter.inlet(body, __metadata__=_metadata(None), __model__=AGENT_MODEL)

    assert result["files"] == [OLD_FILE, NEW_FILE_A]


def test_should_not_declare_file_handler(turn_scope_filter):
    """OpenWebUI deletes every file after the inlet when a filter sets ``file_handler``; scoping must not."""
    assert not hasattr(turn_scope_filter, "file_handler")
