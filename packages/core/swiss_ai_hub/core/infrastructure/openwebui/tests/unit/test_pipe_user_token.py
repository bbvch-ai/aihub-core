"""The OpenWebUI pipe passes the user's Keycloak access token on as X-AIHub-User-Token, so an MCP agent profile with
auth_mode 'user_token' can call its server as that user. Accounts that did not log in through SSO have none."""

import importlib.util
import sys
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

pytestmark = pytest.mark.unit

REPO_ROOT = Path(__file__).resolve().parents[8]
TEMPLATE_PIPE = REPO_ROOT / "infra/deployment/templates/openwebui_functions/aihub_pipeline.py"
OPEN_WEBUI_MODULES = ["open_webui", "open_webui.models", "open_webui.models.chats", "open_webui.models.files"]
OPEN_WEBUI_MODULES += ["open_webui.models.users", "open_webui.utils", "open_webui.utils.chat_id"]
OPEN_WEBUI_MODULES += ["open_webui.models.notes", "open_webui.models.access_grants", "open_webui.models.folders"]
OPEN_WEBUI_MODULES += [
    "open_webui.utils.misc",
    "open_webui.utils.access_control",
    "open_webui.utils.access_control.folders",
]

USER = {"id": "owui-user-1", "name": "Alice Example", "email": "alice@example.com"}
METADATA = {"chat_id": "local:chat-1", "message_id": "message-1"}
OAUTH_SESSION = {"access_token": "eyJ.alice.access", "refresh_token": "eyJ.alice.refresh", "token_type": "Bearer"}


@pytest.fixture
def pipe_module(monkeypatch: pytest.MonkeyPatch) -> Any:
    monkeypatch.setenv("S3_ENDPOINT_URL", "http://s3.test:9000")
    for name in OPEN_WEBUI_MODULES:
        monkeypatch.setitem(sys.modules, name, MagicMock())
    sys.modules["open_webui.utils.chat_id"].is_saved_chat_id = lambda _: False
    spec = importlib.util.spec_from_file_location("aihub_pipeline", TEMPLATE_PIPE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def pipeline(pipe_module: Any) -> Any:
    pipeline = pipe_module.Pipe()
    pipeline._file_service.prepare_files_for_event = AsyncMock(return_value=([], []))
    pipeline._knowledge_reference_service.references_for_event = AsyncMock(return_value=[])
    pipeline._check_open_chat_hitl = AsyncMock(return_value=None)
    pipeline._streaming_service.stream_response = AsyncMock()
    return pipeline


async def _headers_sent_to_the_agent(pipeline: Any, oauth_token: dict[str, Any] | None) -> dict[str, str]:
    await pipeline.pipe(
        body={"model": "aihub.McpReactAgent.lcdm", "messages": [{"role": "user", "content": "Hello"}]},
        __user__=USER,
        __metadata__=METADATA,
        __event_emitter__=AsyncMock(),
        __event_call__=AsyncMock(),
        __oauth_token__=oauth_token,
    )
    return pipeline._streaming_service.stream_response.await_args.args[4]


def test_prepare_headers_adds_the_user_token_only_when_there_is_one(pipe_module: Any) -> None:
    auth = pipe_module.AuthenticationService(signing_secret="secret", api_key="sk-shared")

    with_token = auth.prepare_headers("Alice", "alice@example.com", user_token="eyJ.alice")
    without_token = auth.prepare_headers("Alice", "alice@example.com")

    assert with_token["X-AIHub-User-Token"] == "eyJ.alice"
    assert "X-AIHub-User-Token" not in without_token
    assert with_token["Authorization"] == without_token["Authorization"] == "Bearer sk-shared"


@pytest.mark.asyncio
async def test_a_user_who_logged_in_through_sso_reaches_the_agent_with_their_access_token(pipeline: Any) -> None:
    headers = await _headers_sent_to_the_agent(pipeline, OAUTH_SESSION)

    assert headers["X-AIHub-User-Token"] == "eyJ.alice.access"
    assert OAUTH_SESSION["refresh_token"] not in headers.values()


@pytest.mark.asyncio
async def test_a_local_account_reaches_the_agent_without_a_user_token(pipeline: Any) -> None:
    headers = await _headers_sent_to_the_agent(pipeline, None)

    assert "X-AIHub-User-Token" not in headers
