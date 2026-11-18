"""How the OpenWebUI pipes sign the user they act for, and that the API accepts what they sign.

The API refuses a signature older than a few minutes, so a pipe signs each request as httpx sends it rather than when
it builds the headers: the answer to a dialog reuses the headers of the turn that opened it, however long ago that was.
The pipes import Open WebUI's own modules, which only exist inside that container, so they are stubbed to load them.
"""

import importlib.util
import sys
import time
from collections.abc import Callable
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from fastapi import Request

from swiss_ai_hub.core.auth.dependencies.open_webui_auth_handler.open_webui_auth_handler import OpenWebuiAuthHandler
from swiss_ai_hub.core.auth.dependencies.open_webui_auth_handler.open_webui_signature_rejected_error import (
    OpenWebuiSignatureRejectedError,
)
from swiss_ai_hub.core.auth.dependencies.token_auth_handler.token_auth_handler import TokenAuthHandler

pytestmark = pytest.mark.unit

REPO_ROOT = Path(__file__).resolve().parents[8]
FUNCTIONS = REPO_ROOT / "infra/deployment/templates/openwebui_functions"
OPEN_WEBUI_MODULES = ["open_webui", "open_webui.models", "open_webui.models.chats", "open_webui.models.files"]
OPEN_WEBUI_MODULES += ["open_webui.models.users", "open_webui.utils", "open_webui.utils.chat_id"]
OPEN_WEBUI_MODULES += ["open_webui.models.notes", "open_webui.models.access_grants", "open_webui.models.folders"]
OPEN_WEBUI_MODULES += [
    "open_webui.utils.misc",
    "open_webui.utils.access_control",
    "open_webui.utils.access_control.folders",
]

SIGNING_SECRET = "s" * 64
USER_NAME, USER_EMAIL = "Zoë Keller", "zoe.keller@example.com"
AN_HOUR = 3600


def _load(monkeypatch: pytest.MonkeyPatch, pipe_file: str) -> Any:
    for name in OPEN_WEBUI_MODULES:
        monkeypatch.setitem(sys.modules, name, MagicMock())
    path = FUNCTIONS / pipe_file
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def pipe(monkeypatch: pytest.MonkeyPatch) -> Any:
    return _load(monkeypatch, "aihub_pipeline.py")


@pytest.fixture(params=["aihub_pipeline.py", "openai_pipeline.py"])
def any_pipe(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch) -> Any:
    return _load(monkeypatch, request.param)


@pytest.fixture
def api_handler(monkeypatch: pytest.MonkeyPatch) -> OpenWebuiAuthHandler:
    monkeypatch.setenv("AUTH_OPEN_WEBUI_SIGNING_SECRET", SIGNING_SECRET)
    return OpenWebuiAuthHandler(base_auth_handler=TokenAuthHandler())


@pytest.fixture
def pipe_clock(monkeypatch: pytest.MonkeyPatch, pipe: Any) -> list[int]:
    """The pipe's clock alone, so the API side in the same test keeps the real one."""
    now = [int(time.time())]
    monkeypatch.setattr(pipe, "time", SimpleNamespace(time=lambda: now[0]))
    return now


API_ANSWERS: dict[str, Any] = {
    "/api/v1/my-tenants/active": {"id": "tenant-1"},
    "/api/v1/active/knowledge/openwebui-references": [{"database": "hr", "namespace": "policies"}],
    "/api/v1/active/agents/classes/RAGAgent/instances/hr/files/upload/validate": {"missing": []},
    "/api/v1/active/agents/classes/RAGAgent/instances/hr/files/upload/initiate": {
        "file_id": "f1",
        "upload_url": "http://s3/agent-bucket/f1",
    },
}


@pytest.fixture
def sent(monkeypatch: pytest.MonkeyPatch) -> list[httpx.Request]:
    """Every request a pipe sends, through httpx's real client so its ``auth`` runs as in production."""
    requests: list[httpx.Request] = []
    real_client = httpx.AsyncClient

    def answer(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.host == "s3":
            return httpx.Response(200)
        if request.url.path.endswith("/stream"):
            return httpx.Response(200, text="data: [DONE]\n\n")
        return httpx.Response(200, json=API_ANSWERS[request.url.path])

    def client(**kwargs: Any) -> httpx.AsyncClient:
        return real_client(transport=httpx.MockTransport(answer), **kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", client)
    return requests


def _as_received(request: httpx.Request) -> Request:
    """The request as the API's Starlette parses it."""
    headers = [(name.lower(), value) for name, value in request.headers.raw]
    return Request({"type": "http", "method": request.method, "path": request.url.path, "headers": headers})


def _check_with_the_api(api_handler: OpenWebuiAuthHandler, request: httpx.Request) -> None:
    received = _as_received(request)
    api_handler._reject_unless_recently_signed(
        received,
        received.headers["X-OpenWebUI-Signature"],
        received.headers["X-OpenWebUI-User-Name"],
        received.headers["X-OpenWebUI-User-Email"],
    )


def _hitl_context(pipe: Any, auth: Any, streaming: Any) -> Any:
    return pipe.EventContext(
        state_manager=pipe.StreamingStateManager(),
        emitter=AsyncMock(),
        caller=AsyncMock(),
        headers=auth.prepare_headers(USER_NAME, USER_EMAIL),
        agent_class="RAGAgent",
        agent_id="hr",
        thread_id="65f1c0ffee00000000000001",
        stream_service=streaming,
    )


def test_the_api_accepts_what_either_pipe_signs(any_pipe: Any, api_handler: OpenWebuiAuthHandler) -> None:
    auth = any_pipe.AuthenticationService(SIGNING_SECRET, "api-key")
    request = httpx.Request("POST", "http://api/chat", headers=auth.prepare_headers(USER_NAME, USER_EMAIL))

    _check_with_the_api(api_handler, auth.sign_request(request))


def test_headers_built_but_not_yet_sent_carry_no_signature(any_pipe: Any) -> None:
    headers = any_pipe.AuthenticationService(SIGNING_SECRET, "api-key").prepare_headers(USER_NAME, USER_EMAIL)

    assert "X-OpenWebUI-Signature" not in headers
    assert "X-OpenWebUI-Timestamp" not in headers


@pytest.mark.asyncio
async def test_an_answer_given_an_hour_after_the_dialog_opened_is_accepted(
    pipe: Any, pipe_clock: list[int], sent: list[httpx.Request], api_handler: OpenWebuiAuthHandler
) -> None:
    pipe_clock[0] -= AN_HOUR
    auth = pipe.AuthenticationService(SIGNING_SECRET, "api-key")
    streaming = pipe.StreamingService("http://api", auth, 60)
    context = _hitl_context(pipe, auth, streaming)
    pipe_clock[0] += AN_HOUR

    await streaming.send_hitl_response(
        "HumanInTheLoopResponseEvent", {"approved": True}, "d1", context, "RAGAgent", "hr"
    )

    (answer,) = sent
    assert answer.headers["X-OpenWebUI-Timestamp"] == str(pipe_clock[0])
    _check_with_the_api(api_handler, answer)


def test_a_signature_made_when_the_dialog_opened_would_be_refused(
    pipe: Any, pipe_clock: list[int], api_handler: OpenWebuiAuthHandler
) -> None:
    """The failure signing at send time avoids, shown with the same clock."""
    auth = pipe.AuthenticationService(SIGNING_SECRET, "api-key")
    request = httpx.Request("POST", "http://api/chat", headers=auth.prepare_headers(USER_NAME, USER_EMAIL))
    pipe_clock[0] -= AN_HOUR

    with pytest.raises(OpenWebuiSignatureRejectedError, match="Expired"):
        _check_with_the_api(api_handler, auth.sign_request(request))


@pytest.mark.asyncio
async def test_a_file_upload_signs_its_api_call_but_not_the_storage_upload(
    pipe: Any, sent: list[httpx.Request], api_handler: OpenWebuiAuthHandler
) -> None:
    auth = pipe.AuthenticationService(SIGNING_SECRET, "api-key")
    service = pipe.FileProcessingService("http://api", auth, "http://s3", "key", "secret")
    attachment = pipe.AgentAttachment(source={}, filename="notes.txt", content_type="text/plain", text="notes")

    await service._upload(attachment, "RAGAgent", "hr", auth.prepare_headers(USER_NAME, USER_EMAIL))

    initiate, storage_upload = sent
    _check_with_the_api(api_handler, initiate)
    assert "X-OpenWebUI-Signature" not in storage_upload.headers


@pytest.mark.parametrize(
    ("call", "answer"),
    [
        (
            lambda pipe, auth, headers: pipe.StreamingService("http://api", auth, 60).active_tenant_id(headers),
            "tenant-1",
        ),
        (
            lambda pipe, auth, headers: pipe.KnowledgeReferenceService("http://api", auth).references_for_event(
                [{"type": "collection", "id": "k1"}], headers
            ),
            [{"database": "hr", "namespace": "policies"}],
        ),
        (
            lambda pipe, auth, headers: pipe.FileProcessingService("http://api", auth, "http://s3", "k", "s")._missing(
                [pipe.AgentAttachment(source={}, filename="a.pdf", content_type="application/pdf", file_id="f1")],
                "RAGAgent",
                "hr",
                headers,
                "65f1c0ffee00000000000001",
            ),
            set(),
        ),
    ],
    ids=["active tenant", "knowledge references", "file validation"],
)
@pytest.mark.asyncio
async def test_every_api_call_of_a_turn_is_signed(
    pipe: Any, sent: list[httpx.Request], api_handler: OpenWebuiAuthHandler, call: Callable[..., Any], answer: Any
) -> None:
    auth = pipe.AuthenticationService(SIGNING_SECRET, "api-key")

    assert await call(pipe, auth, auth.prepare_headers(USER_NAME, USER_EMAIL)) == answer

    (request,) = sent
    _check_with_the_api(api_handler, request)
