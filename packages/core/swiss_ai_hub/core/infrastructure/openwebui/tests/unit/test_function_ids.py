"""Unit tests that the OpenWebUI functions load without ``bson`` and keep deriving the same ids.

Open WebUI 0.11.4 no longer installs pymongo, so a function importing ``bson`` fails to load. The derived thread and
display ids must stay byte-identical to the ``bson.ObjectId`` form they replace: the AI-Hub frontend resolves a thread
from the ids already persisted with its events.
"""

import hashlib
import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from unittest.mock import MagicMock

import pytest
from bson import ObjectId

pytestmark = pytest.mark.unit

FUNCTIONS_DIR = Path(__file__).resolve().parents[8] / "infra/deployment/templates/openwebui_functions"
OPEN_WEBUI_MODULES = ["open_webui", "open_webui.models", "open_webui.models.chats", "open_webui.models.files"]
OPEN_WEBUI_MODULES += ["open_webui.models.models", "open_webui.models.users"]
OPEN_WEBUI_MODULES += ["open_webui.utils", "open_webui.utils.chat_id"]

HASHING_HELPERS = [
    ("aihub_pipeline", "Pipe", "_str_to_object_id"),
    ("aihub_pipeline", "ResponseMergeService", "_str_to_object_id"),
    ("openai_pipeline", "Pipe", "_str_to_object_id"),
    ("memory_action", "Action", "_str_to_object_id"),
    ("files_action", "Action", "_str_to_object_id"),
    ("source_action", "Action", "_str_to_object_id"),
    ("tracing_action", "Action", "_str_to_object_id"),
]
DISPLAY_ID_HELPERS = [*HASHING_HELPERS, ("aihub_ui_context_filter", "Filter", "_display_id")]


def _load_without_bson(monkeypatch: pytest.MonkeyPatch, name: str) -> ModuleType:
    for module_name in OPEN_WEBUI_MODULES:
        monkeypatch.setitem(sys.modules, module_name, MagicMock())
    monkeypatch.setitem(sys.modules, "bson", None)
    spec = importlib.util.spec_from_file_location(name, FUNCTIONS_DIR / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _helper(monkeypatch: pytest.MonkeyPatch, name: str, class_name: str, method: str):
    owner = getattr(_load_without_bson(monkeypatch, name), class_name)
    return getattr(owner.__new__(owner), method)


@pytest.mark.parametrize(("name", "class_name", "method"), DISPLAY_ID_HELPERS)
def test_display_id_matches_the_object_id_it_replaces(
    monkeypatch: pytest.MonkeyPatch, name: str, class_name: str, method: str
) -> None:
    expected = str(ObjectId(hashlib.md5(b":message-1").digest()[:12])).lower()

    assert _helper(monkeypatch, name, class_name, method)("message-1") == expected


@pytest.mark.parametrize(("name", "class_name", "method"), HASHING_HELPERS)
def test_thread_id_matches_the_object_id_it_replaces(
    monkeypatch: pytest.MonkeyPatch, name: str, class_name: str, method: str
) -> None:
    helper = _helper(monkeypatch, name, class_name, method)
    if "salt" not in helper.__code__.co_varnames:
        pytest.skip("this helper derives display ids only")
    expected = str(ObjectId(hashlib.md5(b"agent-x:chat-1").digest()[:12])).lower()

    assert helper("chat-1", salt="agent-x") == expected


@pytest.mark.parametrize(("name", "class_name", "method"), HASHING_HELPERS)
def test_missing_context_still_yields_a_parsable_object_id(
    monkeypatch: pytest.MonkeyPatch, name: str, class_name: str, method: str
) -> None:
    generated = _helper(monkeypatch, name, class_name, method)(None)

    assert str(ObjectId(generated)) == generated
