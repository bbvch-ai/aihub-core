import json
from types import SimpleNamespace

import httpx
import pytest
from fastapi import HTTPException
from pydantic import SecretStr
from swiss_ai_hub.core.infrastructure.openwebui import OpenWebuiModPackage

from swiss_ai_hub.sysadmin_api.routes.openwebui_mods import openwebui_mod_service
from swiss_ai_hub.sysadmin_api.routes.openwebui_mods.openwebui_mod_service import OpenWebuiModService


@pytest.mark.asyncio
async def test_compilation_sends_source_with_service_authentication(monkeypatch: pytest.MonkeyPatch) -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        assert request.url == "http://openwebui.test/_aihub/mods/control/compile"
        assert request.headers["authorization"] == "Bearer compiler-test-token"
        assert request.content == b"stored source"
        return httpx.Response(200, content=b"compiled archive", headers={"Content-Type": "application/zip"})

    client = httpx.AsyncClient
    monkeypatch.setattr(openwebui_mod_service, "OpenWebuiSettings", lambda: SimpleNamespace(
        BASE_URL="http://openwebui.test/", SCIM_TOKEN=SecretStr("compiler-test-token"),
    ))
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: client(transport=httpx.MockTransport(respond), **kwargs))
    assert await OpenWebuiModService._compile(b"stored source") == b"compiled archive"


@pytest.mark.asyncio
@pytest.mark.parametrize("status,content,content_type,expected", [
    (422, b'{"detail":"Menu.svelte: invalid syntax"}', "application/json", 422),
    (429, b'{"detail":"Another mod is compiling"}', "application/json", 429),
    (504, b'{"detail":"Compilation timed out"}', "application/json", 504),
    (502, b"upstream unavailable", "text/plain", 502),
    (200, b"not a publication", "text/html", 502),
])
async def test_compiler_errors_retain_their_meaning(
    monkeypatch: pytest.MonkeyPatch, status: int, content: bytes, content_type: str, expected: int,
) -> None:
    client = httpx.AsyncClient
    transport = httpx.MockTransport(lambda request: httpx.Response(status, content=content, headers={"Content-Type": content_type}))
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: client(transport=transport, **kwargs))
    with pytest.raises(HTTPException) as caught:
        await OpenWebuiModService._compile(b"stored source")
    assert caught.value.status_code == expected
    if content_type == "application/json":
        assert caught.value.detail == json.loads(content)["detail"]


@pytest.mark.asyncio
async def test_compiler_output_size_is_bounded(monkeypatch: pytest.MonkeyPatch) -> None:
    client = httpx.AsyncClient
    transport = httpx.MockTransport(lambda request: httpx.Response(200, content=b"oversized", headers={"Content-Type": "application/zip"}))
    monkeypatch.setattr(OpenWebuiModPackage, "MAX_ARCHIVE_BYTES", 8)
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: client(transport=transport, **kwargs))
    with pytest.raises(HTTPException) as caught:
        await OpenWebuiModService._compile(b"source")
    assert caught.value.status_code == 502
