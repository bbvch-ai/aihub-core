"""The pipe forwards the user's own Keycloak access token, so an MCP connection with auth_mode 'user_token' (required by
forward_tenant_id_header) can run from a chat.

The pipe imports Open WebUI's own modules, which only exist inside that container, so they are stubbed to load it
from its file path.
"""

import importlib.util
import sys
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from swiss_ai_hub.core.tracing import NATSMessageHeaders

pytestmark = pytest.mark.unit

REPO_ROOT = Path(__file__).resolve().parents[8]
TEMPLATE_PIPE = REPO_ROOT / "infra/deployment/templates/openwebui_functions/aihub_pipeline.py"
OPEN_WEBUI_MODULES = ["open_webui", "open_webui.models", "open_webui.models.chats", "open_webui.models.files"]
OPEN_WEBUI_MODULES += ["open_webui.models.users", "open_webui.utils", "open_webui.utils.chat_id"]
AGENT_USER_TOKEN_HEADER = "x-aihub-user-token"


@pytest.fixture
def pipe(monkeypatch: pytest.MonkeyPatch) -> Any:
    for name in OPEN_WEBUI_MODULES:
        monkeypatch.setitem(sys.modules, name, MagicMock())
    spec = importlib.util.spec_from_file_location("aihub_pipeline", TEMPLATE_PIPE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_access_token_is_forwarded_under_the_header_the_agent_reads(pipe: Any) -> None:
    headers = pipe.AuthenticationService.user_token_headers({"access_token": "user-jwt", "id_token": "id-jwt"})

    assert headers == {"X-AIHub-User-Token": "user-jwt"}
    assert NATSMessageHeaders.extract_aihub_headers(headers) == {AGENT_USER_TOKEN_HEADER: "user-jwt"}


@pytest.mark.parametrize("oauth_token", [None, {}, {"access_token": ""}, {"id_token": "id-jwt"}])
def test_no_header_without_an_access_token(pipe: Any, oauth_token: dict[str, Any] | None) -> None:
    assert pipe.AuthenticationService.user_token_headers(oauth_token) == {}
