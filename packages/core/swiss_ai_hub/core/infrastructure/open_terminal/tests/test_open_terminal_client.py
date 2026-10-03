"""How the open-terminal client talks to the sandbox: always as one user, never as the shared fallback account."""

from typing import Any

import httpx
import pytest
from pydantic import SecretStr

from swiss_ai_hub.core.infrastructure.open_terminal import open_terminal_client
from swiss_ai_hub.core.infrastructure.open_terminal.open_terminal_client import OpenTerminalClient
from swiss_ai_hub.core.infrastructure.open_terminal.open_terminal_error import OpenTerminalError
from swiss_ai_hub.core.infrastructure.open_terminal.open_terminal_settings import OpenTerminalSettings

pytestmark = pytest.mark.unit


class _Sandbox:
    """Answers like the sandbox and records what it was sent."""

    def __init__(self) -> None:
        self.requests: list[httpx.Request] = []
        self.timeouts: list[Any] = []


@pytest.fixture
def sandbox(monkeypatch: pytest.MonkeyPatch) -> _Sandbox:
    recorded = _Sandbox()

    def respond(request: httpx.Request) -> httpx.Response:
        recorded.requests.append(request)
        if request.url.path == "/files/view":
            return httpx.Response(200, content=b"%PDF", headers={"content-type": "application/pdf"})
        if request.url.params.get("path") == "missing.txt":
            return httpx.Response(404, json={"detail": "File not found"})
        return httpx.Response(200, json={"ok": True})

    real_client = httpx.AsyncClient

    def client(**kwargs: Any) -> httpx.AsyncClient:
        recorded.timeouts.append(kwargs["timeout"])
        return real_client(transport=httpx.MockTransport(respond), **kwargs)

    monkeypatch.setattr(open_terminal_client.httpx, "AsyncClient", client)
    return recorded


def _client() -> OpenTerminalClient:
    settings = OpenTerminalSettings(BASE_URL="http://sandbox:8000", API_KEY=SecretStr("key"), TIMEOUT=30)
    return OpenTerminalClient("owui-user-1", settings)


@pytest.mark.asyncio
async def test_every_request_names_the_user_and_carries_the_key(sandbox: _Sandbox) -> None:
    await _client().list_files("conversations/t1")

    assert sandbox.requests[0].headers["x-user-id"] == "owui-user-1"
    assert sandbox.requests[0].headers["authorization"] == "Bearer key"


@pytest.mark.asyncio
async def test_unset_options_are_left_to_the_sandbox(sandbox: _Sandbox) -> None:
    await _client().read_file("notes.txt")

    assert dict(sandbox.requests[0].url.params) == {"path": "notes.txt"}


@pytest.mark.asyncio
async def test_a_command_may_take_its_wait_on_top_of_the_timeout(sandbox: _Sandbox) -> None:
    await _client().execute("python3 run.py", cwd="conversations/t1", wait=60)

    assert sandbox.requests[0].url.params["wait"] == "60"
    assert sandbox.timeouts == [90]


@pytest.mark.asyncio
async def test_a_refusal_carries_the_sandbox_reason(sandbox: _Sandbox) -> None:
    client = _client()

    with pytest.raises(OpenTerminalError, match="404: File not found"):
        await client.read_file("missing.txt")


@pytest.mark.asyncio
async def test_viewing_returns_the_raw_bytes_of_any_file(sandbox: _Sandbox) -> None:
    assert await _client().view("report.pdf") == (b"%PDF", "application/pdf")
