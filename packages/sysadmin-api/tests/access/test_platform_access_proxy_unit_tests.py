from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from fastapi import HTTPException
from swiss_ai_hub.api import AccessCapabilitiesRequest

from swiss_ai_hub.sysadmin_api.routes.access.platform_access_proxy import PlatformAccessProxy

_CLIENT = "swiss_ai_hub.sysadmin_api.routes.access.platform_access_proxy.httpx.AsyncClient"


def _request(headers: dict[str, str]) -> SimpleNamespace:
    return SimpleNamespace(headers=headers)


def test_forward_headers_keeps_only_auth_and_locale():
    request = _request(
        {
            "authorization": "Bearer abc",
            "lang": "fr",
            "cookie": "session=secret",
            "host": "sysadmin.example",
        }
    )

    assert PlatformAccessProxy._forward_headers(request) == {"authorization": "Bearer abc", "lang": "fr"}


def _mock_client(json_payload: object) -> tuple[AsyncMock, AsyncMock]:
    response = SimpleNamespace(raise_for_status=lambda: None, json=lambda: json_payload)
    client = AsyncMock()
    client.post.return_value = response
    client.get.return_value = response
    context = AsyncMock()
    context.__aenter__.return_value = client
    return context, client


@pytest.mark.asyncio
async def test_fetch_capabilities_forwards_token_body_and_tenant():
    context, client = _mock_client({"groups": []})
    request = _request({"authorization": "Bearer xyz", "lang": "de"})
    body = AccessCapabilitiesRequest(access_rules=["aihub.admin.>"], restrict_to_tenant=False)

    with patch(_CLIENT, return_value=context):
        result = await PlatformAccessProxy.fetch_capabilities("http://api:8000", "default", request, body)

    assert result.groups == []
    client.post.assert_awaited_once()
    _, kwargs = client.post.call_args
    assert client.post.call_args.args[0] == "/api/v1/default/access/capabilities"
    assert kwargs["json"] == body.model_dump()
    assert kwargs["headers"] == {"authorization": "Bearer xyz", "lang": "de"}


@pytest.mark.asyncio
async def test_fetch_presets_proxies_to_main_api():
    payload = [{"rule": "aihub.user.>", "name": "Use everything", "description": "d", "category": "everything"}]
    context, client = _mock_client(payload)
    request = _request({"authorization": "Bearer xyz"})

    with patch(_CLIENT, return_value=context):
        result = await PlatformAccessProxy.fetch_presets("http://api:8000", "active", request)

    assert [preset.rule for preset in result] == ["aihub.user.>"]
    assert client.get.call_args.args[0] == "/api/v1/active/access/presets"


@pytest.mark.asyncio
async def test_fetch_capabilities_passes_through_upstream_status():
    upstream = httpx.Response(403, text="forbidden", request=httpx.Request("POST", "http://api:8000/x"))

    def _raise_403():
        raise httpx.HTTPStatusError("403", request=upstream.request, response=upstream)

    response = SimpleNamespace(raise_for_status=_raise_403, json=lambda: {})
    client = AsyncMock()
    client.post.return_value = response
    context = AsyncMock()
    context.__aenter__.return_value = client
    body = AccessCapabilitiesRequest(access_rules=[], restrict_to_tenant=True)

    with patch(_CLIENT, return_value=context), pytest.raises(HTTPException) as raised:
        await PlatformAccessProxy.fetch_capabilities("http://api:8000", "active", _request({}), body)

    assert raised.value.status_code == 403


@pytest.mark.asyncio
async def test_fetch_presets_maps_network_failure_to_502():
    client = AsyncMock()
    client.get.side_effect = httpx.ConnectError("connection refused")
    context = AsyncMock()
    context.__aenter__.return_value = client

    with patch(_CLIENT, return_value=context), pytest.raises(HTTPException) as raised:
        await PlatformAccessProxy.fetch_presets("http://api:8000", "active", _request({}))

    assert raised.value.status_code == 502
