import httpx
import pytest

from swiss_ai_hub.core.infrastructure.openwebui.openwebui_session_lookup import OpenWebuiSessionLookup

pytestmark = pytest.mark.unit

BASE_URL = "http://open-webui:8080"


def _lookup_answering(status_code: int, body: dict | None = None) -> tuple[OpenWebuiSessionLookup, list[httpx.Request]]:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(status_code, json=body or {})

    return OpenWebuiSessionLookup(BASE_URL, transport=httpx.MockTransport(handler)), requests


@pytest.mark.asyncio
async def test_should_return_the_session_email_when_openwebui_accepts_the_token() -> None:
    lookup, requests = _lookup_answering(200, {"id": "u1", "email": "ada@example.com"})

    email = await lookup.email_of("session-token")

    assert email == "ada@example.com"
    assert str(requests[0].url) == f"{BASE_URL}/api/v1/auths/"
    assert requests[0].headers["Authorization"] == "Bearer session-token"


@pytest.mark.asyncio
@pytest.mark.parametrize("status_code", [401, 403])
async def test_should_return_none_when_openwebui_rejects_the_token(status_code: int) -> None:
    lookup, _ = _lookup_answering(status_code)

    assert await lookup.email_of("expired-token") is None


@pytest.mark.asyncio
async def test_should_raise_when_openwebui_fails() -> None:
    lookup, _ = _lookup_answering(500)

    with pytest.raises(httpx.HTTPStatusError):
        await lookup.email_of("session-token")
