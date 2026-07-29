from collections.abc import Iterator
from unittest.mock import MagicMock, patch

import httpx
import pytest

from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.infrastructure.litellm.lite_llm_service import LiteLLMService

pytestmark = pytest.mark.unit


class _RecordingTransport(httpx.MockTransport):
    """MockTransport that records every request path so call expectations can be asserted."""

    def __init__(self, responses: dict[str, httpx.Response]) -> None:
        self.requests: list[tuple[str, str]] = []

        def handler(request: httpx.Request) -> httpx.Response:
            self.requests.append((request.method, request.url.path))
            return responses[request.url.path]

        super().__init__(handler)


def _user(user_id: str) -> UserIdentity:
    return UserIdentity(id=user_id, name="Ada Lovelace", email="ada@example.com", roles=[])


@pytest.fixture(autouse=True)
def _clear_cache() -> Iterator[None]:
    LiteLLMService._user_cache.clear()
    yield
    LiteLLMService._user_cache.clear()


def _patched_settings(transport: _RecordingTransport) -> MagicMock:
    settings = MagicMock()
    settings.httpx_aclient = httpx.AsyncClient(base_url="http://litellm:4000", transport=transport)
    for attr in (
        "USER_MAX_BUDGET",
        "USER_SOFT_BUDGET",
        "USER_MAX_PARALLEL_REQUESTS",
        "USER_TPM_LIMIT",
        "USER_RPM_LIMIT",
        "USER_BUDGET_DURATION",
    ):
        setattr(settings, attr, None)
    return settings


async def _run(transport: _RecordingTransport, user: UserIdentity) -> str:
    settings = _patched_settings(transport)
    with patch(
        "swiss_ai_hub.core.infrastructure.litellm.lite_llm_service.LiteLLMProxySettings",
        return_value=settings,
    ):
        return await LiteLLMService.api_key_for_user(user)


@pytest.mark.asyncio
async def test_existing_user_returns_deterministic_key_without_provisioning() -> None:
    user = _user("existing-user")
    transport = _RecordingTransport({"/user/info": httpx.Response(200, json={"user_info": {"user_alias": ""}})})

    key = await _run(transport, user)

    assert key == LiteLLMService.generate_key_for_user(user)
    assert transport.requests == [("GET", "/user/info")]


@pytest.mark.asyncio
async def test_absent_user_is_created_with_a_key() -> None:
    user = _user("new-user")
    transport = _RecordingTransport(
        {
            "/user/info": httpx.Response(404, json={"error": "not found"}),
            "/user/new": httpx.Response(200, json={"user_id": "new-user"}),
            "/key/generate": httpx.Response(200, json={"key": "sk-irrelevant"}),
        }
    )

    key = await _run(transport, user)

    assert key == LiteLLMService.generate_key_for_user(user)
    assert transport.requests == [("GET", "/user/info"), ("POST", "/user/new"), ("POST", "/key/generate")]


@pytest.mark.asyncio
async def test_user_new_conflict_still_generates_the_key() -> None:
    user = _user("racing-user")
    transport = _RecordingTransport(
        {
            "/user/info": httpx.Response(404, json={"error": "not found"}),
            "/user/new": httpx.Response(409, json={"error": "user already exists"}),
            "/key/generate": httpx.Response(200, json={"key": "sk-irrelevant"}),
        }
    )

    key = await _run(transport, user)

    assert key == LiteLLMService.generate_key_for_user(user)
    assert transport.requests == [("GET", "/user/info"), ("POST", "/user/new"), ("POST", "/key/generate")]


@pytest.mark.asyncio
async def test_key_generate_conflict_is_treated_as_success() -> None:
    user = _user("racing-key-user")
    transport = _RecordingTransport(
        {
            "/user/info": httpx.Response(404, json={"error": "not found"}),
            "/user/new": httpx.Response(200, json={"user_id": "racing-key-user"}),
            "/key/generate": httpx.Response(409, json={"error": "key already exists"}),
        }
    )

    key = await _run(transport, user)

    assert key == LiteLLMService.generate_key_for_user(user)
    assert transport.requests == [("GET", "/user/info"), ("POST", "/user/new"), ("POST", "/key/generate")]


@pytest.mark.asyncio
async def test_user_info_server_error_propagates_without_caching() -> None:
    user = _user("erroring-user")
    transport = _RecordingTransport({"/user/info": httpx.Response(500, json={"error": "boom"})})

    with pytest.raises(httpx.HTTPStatusError):
        await _run(transport, user)

    assert user.id not in LiteLLMService._user_cache
