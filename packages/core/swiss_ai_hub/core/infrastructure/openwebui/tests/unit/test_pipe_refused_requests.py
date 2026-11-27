"""What a user sees when the API refuses an agent request, such as one from a user Keycloak deleted or disabled while
their OpenWebUI session goes on: the API's reason, kept as the answer, never an empty answer marked completed."""

import importlib.util
import sys
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

pytestmark = pytest.mark.unit

REPO_ROOT = Path(__file__).resolve().parents[8]
TEMPLATE_PIPE = REPO_ROOT / "infra/deployment/templates/openwebui_functions/aihub_pipeline.py"
OPEN_WEBUI_MODULES = ["open_webui", "open_webui.models", "open_webui.models.chats", "open_webui.models.files"]
OPEN_WEBUI_MODULES += ["open_webui.models.users", "open_webui.utils", "open_webui.utils.chat_id"]
OPEN_WEBUI_MODULES += ["open_webui.models.notes", "open_webui.models.access_grants", "open_webui.models.folders"]
OPEN_WEBUI_MODULES += ["open_webui.utils.misc", "open_webui.utils.access_control"]
OPEN_WEBUI_MODULES += ["open_webui.utils.access_control.folders"]


@pytest.fixture
def pipe(monkeypatch: pytest.MonkeyPatch) -> Any:
    for name in OPEN_WEBUI_MODULES:
        monkeypatch.setitem(sys.modules, name, MagicMock())
    spec = importlib.util.spec_from_file_location("aihub_pipeline", TEMPLATE_PIPE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _api_answering(monkeypatch: pytest.MonkeyPatch, answer: Any) -> None:
    real_client = httpx.AsyncClient
    monkeypatch.setattr(
        httpx, "AsyncClient", lambda **kwargs: real_client(transport=httpx.MockTransport(answer), **kwargs)
    )


async def _stream(pipe: Any, emitter: AsyncMock, state_manager: Any) -> bool:
    auth = pipe.AuthenticationService("s" * 64, "api-key")
    return await pipe.StreamingService("http://api", auth, 60).stream_response(
        "LLMWrappingAgent",
        "assistant",
        "UserMessageEvent",
        {"content": "Are you still there?"},
        auth.prepare_headers("Deleted User", "deleted.user@example.com"),
        "65f1c0ffee00000000000001",
        "65f1c0ffee00000000000002",
        emitter,
        AsyncMock(),
        state_manager,
    )


def _statuses(emitter: AsyncMock) -> list[dict[str, Any]]:
    return [call.args[0]["data"] for call in emitter.await_args_list if call.args[0]["type"] == "status"]


@pytest.mark.asyncio
async def test_a_refused_request_keeps_the_apis_reason_as_the_answer(
    pipe: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    _api_answering(monkeypatch, lambda request: httpx.Response(403, json={"detail": "This account is disabled."}))
    state_manager, emitter = pipe.StreamingStateManager(), AsyncMock()

    completed = await _stream(pipe, emitter, state_manager)

    assert not completed
    assert "This account is disabled." in state_manager.serialize_to_html()
    assert _statuses(emitter)[-1]["error"]


@pytest.mark.asyncio
async def test_a_stream_that_breaks_off_keeps_the_error_as_the_answer(
    pipe: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    def unreachable(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("API unreachable", request=request)

    _api_answering(monkeypatch, unreachable)
    state_manager, emitter = pipe.StreamingStateManager(), AsyncMock()

    completed = await _stream(pipe, emitter, state_manager)

    assert not completed
    assert "API unreachable" in state_manager.serialize_to_html()
    assert _statuses(emitter)[-1]["error"]


@pytest.mark.asyncio
async def test_a_stream_the_api_accepts_is_reported_as_completed(pipe: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    _api_answering(monkeypatch, lambda request: httpx.Response(200, text="data: [DONE]\n\n"))

    assert await _stream(pipe, AsyncMock(), pipe.StreamingStateManager())
