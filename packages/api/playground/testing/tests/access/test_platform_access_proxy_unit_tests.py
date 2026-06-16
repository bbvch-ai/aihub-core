from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from swiss_ai_hub.api.routes.access.dto.access_capabilities_request import AccessCapabilitiesRequest
from swiss_ai_hub.api.routes.access.platform_access_proxy import PlatformAccessProxy


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

    with patch("swiss_ai_hub.api.routes.access.platform_access_proxy.httpx.AsyncClient", return_value=context):
        result = await PlatformAccessProxy.fetch_capabilities("http://api:8000", "default", request, body)

    assert result.groups == []
    client.post.assert_awaited_once()
    _, kwargs = client.post.call_args
    assert client.post.call_args.args[0] == "/api/v1/default/roles/access/capabilities"
    assert kwargs["json"] == body.model_dump()
    assert kwargs["headers"] == {"authorization": "Bearer xyz", "lang": "de"}


@pytest.mark.asyncio
async def test_fetch_presets_proxies_to_main_api():
    payload = [{"rule": "aihub.user.>", "name": "Use everything", "description": "d", "category": "everything"}]
    context, client = _mock_client(payload)
    request = _request({"authorization": "Bearer xyz"})

    with patch("swiss_ai_hub.api.routes.access.platform_access_proxy.httpx.AsyncClient", return_value=context):
        result = await PlatformAccessProxy.fetch_presets("http://api:8000", "active", request)

    assert [preset.rule for preset in result] == ["aihub.user.>"]
    assert client.get.call_args.args[0] == "/api/v1/active/roles/access/presets"
