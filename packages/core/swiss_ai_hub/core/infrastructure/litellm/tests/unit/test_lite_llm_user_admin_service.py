import json
from collections.abc import AsyncIterator, Callable
from unittest.mock import MagicMock, patch

import httpx
import pytest
import pytest_asyncio

from swiss_ai_hub.core.infrastructure.litellm.lite_llm_user_admin_service import LiteLLMUserAdminService
from swiss_ai_hub.core.infrastructure.litellm.lite_llm_user_limits import LiteLLMUserLimits

pytestmark = pytest.mark.unit

FLAG = LiteLLMUserAdminService.KEYS_BLOCKED_BY_HUB


class _RecordingTransport(httpx.MockTransport):
    """Answers each path with its responses in order and records every request with its query and JSON body."""

    def __init__(self, responses: dict[str, list[httpx.Response]]) -> None:
        self.requests: list[tuple[str, str, dict, dict | None]] = []

        def handler(request: httpx.Request) -> httpx.Response:
            body = json.loads(request.content) if request.content else None
            self.requests.append((request.method, request.url.path, dict(request.url.params), body))
            return responses[request.url.path].pop(0)

        super().__init__(handler)

    def bodies(self, path: str) -> list[dict | None]:
        return [body for _, request_path, _, body in self.requests if request_path == path]


@pytest_asyncio.fixture
async def gateway() -> AsyncIterator[Callable[[dict[str, list[httpx.Response]]], _RecordingTransport]]:
    """Routes the service's master-key client through a recording transport built from the given responses."""
    clients: list[httpx.AsyncClient] = []

    def install(responses: dict[str, list[httpx.Response]]) -> _RecordingTransport:
        transport = _RecordingTransport(responses)
        settings = MagicMock()
        settings.httpx_aclient = httpx.AsyncClient(base_url="http://litellm:4000", transport=transport)
        clients.append(settings.httpx_aclient)
        patcher.return_value = settings
        return transport

    with patch("swiss_ai_hub.core.infrastructure.litellm.lite_llm_user_admin_service.LiteLLMProxySettings") as patcher:
        yield install
    for client in clients:
        await client.aclose()


def _ok(payload: dict | None = None) -> httpx.Response:
    return httpx.Response(200, json=payload or {})


@pytest.mark.asyncio
async def test_unchanged_limits_send_nothing(gateway) -> None:
    transport = gateway({})
    limits = LiteLLMUserLimits(max_budget=100.0, budget_duration="30d")

    changed = await LiteLLMUserAdminService.update_limits("u1", limits, current=limits.model_copy())

    assert changed is False
    assert transport.requests == []


@pytest.mark.asyncio
async def test_a_limit_change_sends_only_the_changed_fields(gateway) -> None:
    transport = gateway({"/user/update": [_ok()]})
    current = LiteLLMUserLimits(max_budget=100.0, budget_duration="30d", rpm_limit=60)

    changed = await LiteLLMUserAdminService.update_limits(
        "u1", LiteLLMUserLimits(max_budget=100.0, budget_duration="30d", rpm_limit=30), current=current
    )

    assert changed is True
    assert transport.bodies("/user/update") == [{"user_id": "u1", "rpm_limit": 30}]


@pytest.mark.asyncio
async def test_the_users_row_is_read_when_the_caller_does_not_have_it(gateway) -> None:
    """The entry point for limits changed in the Hub (#2135), whose callers hold no LiteLLM row."""
    transport = gateway(
        {
            "/user/info": [_ok({"user_id": "u1", "user_info": {"user_id": "u1", "max_budget": 100.0}})],
            "/user/update": [_ok()],
        }
    )

    await LiteLLMUserAdminService.update_limits("u1", LiteLLMUserLimits(max_budget=20.0))

    assert transport.requests[0][:3] == ("GET", "/user/info", {"user_id": "u1"})
    assert transport.bodies("/user/update") == [{"user_id": "u1", "max_budget": 20.0}]


@pytest.mark.asyncio
async def test_blocking_records_the_usable_keys_before_blocking_them(gateway) -> None:
    """Recording first means a run failing half-way still leaves the record that later unblocks the keys."""
    transport = gateway({"/user/update": [_ok()], "/key/block": [_ok()]})
    user_row = {"user_id": "u1", "metadata": {"note": "kept"}}
    keys = [{"token": "hash-usable", "blocked": None}, {"token": "hash-blocked-by-hand", "blocked": True}]

    blocked = await LiteLLMUserAdminService.block_keys(user_row, keys)

    assert [path for _, path, _, _ in transport.requests] == ["/user/update", "/key/block"]
    assert transport.bodies("/user/update") == [{"user_id": "u1", "metadata": {"note": "kept", FLAG: ["hash-usable"]}}]
    assert transport.bodies("/key/block") == [{"key": "hash-usable"}]
    assert blocked == ["hash-usable"]


@pytest.mark.asyncio
async def test_a_key_minted_after_the_block_joins_the_record(gateway) -> None:
    transport = gateway({"/user/update": [_ok()], "/key/block": [_ok()]})
    user_row = {"user_id": "u1", "metadata": {FLAG: ["hash-old"]}}

    await LiteLLMUserAdminService.block_keys(
        user_row, [{"token": "hash-old", "blocked": True}, {"token": "hash-new", "blocked": False}]
    )

    assert transport.bodies("/user/update") == [{"user_id": "u1", "metadata": {FLAG: ["hash-old", "hash-new"]}}]
    assert transport.bodies("/key/block") == [{"key": "hash-new"}]


@pytest.mark.asyncio
async def test_blocking_a_user_without_usable_keys_changes_nothing(gateway) -> None:
    transport = gateway({})

    blocked = await LiteLLMUserAdminService.block_keys(
        {"user_id": "u1", "metadata": {}}, [{"token": "hash-blocked-by-hand", "blocked": True}]
    )

    assert transport.requests == []
    assert blocked == []


@pytest.mark.asyncio
async def test_unblocking_releases_only_the_recorded_keys_then_clears_the_record(gateway) -> None:
    """LiteLLM ignores an empty metadata, so the record is cleared by setting it to an empty list."""
    transport = gateway({"/key/unblock": [_ok()], "/user/update": [_ok()]})
    keys = [
        {"token": "hash-blocked-by-hub", "blocked": True},
        {"token": "hash-blocked-by-hand", "blocked": True},
        {"token": "hash-usable", "blocked": False},
    ]

    await LiteLLMUserAdminService.unblock_keys({"user_id": "u1", "metadata": {FLAG: ["hash-blocked-by-hub"]}}, keys)

    assert [path for _, path, _, _ in transport.requests] == ["/key/unblock", "/user/update"]
    assert transport.bodies("/key/unblock") == [{"key": "hash-blocked-by-hub"}]
    assert transport.bodies("/user/update") == [{"user_id": "u1", "metadata": {FLAG: []}}]


@pytest.mark.asyncio
async def test_deleting_a_user_already_gone_is_accepted(gateway) -> None:
    gateway({"/user/delete": [httpx.Response(404, json={"detail": {"error": "User not found"}})]})

    await LiteLLMUserAdminService.delete_user("u1")


@pytest.mark.asyncio
async def test_a_failed_delete_propagates(gateway) -> None:
    gateway({"/user/delete": [httpx.Response(500, json={})]})

    with pytest.raises(httpx.HTTPStatusError):
        await LiteLLMUserAdminService.delete_user("u1")


@pytest.mark.asyncio
async def test_users_are_listed_across_every_page(gateway) -> None:
    transport = gateway(
        {
            "/user/list": [
                _ok({"users": [{"user_id": "u1"}], "total_pages": 2}),
                _ok({"users": [{"user_id": "u2"}], "total_pages": 2}),
            ]
        }
    )

    users = await LiteLLMUserAdminService.list_users()

    assert [user["user_id"] for user in users] == ["u1", "u2"]
    assert [params["page"] for _, _, params, _ in transport.requests] == ["1", "2"]


@pytest.mark.asyncio
async def test_keys_are_listed_as_full_objects(gateway) -> None:
    transport = gateway({"/key/list": [_ok({"keys": [{"token": "hash", "user_id": "u1"}], "total_pages": 1})]})

    keys = await LiteLLMUserAdminService.list_keys()

    assert keys == [{"token": "hash", "user_id": "u1"}]
    assert transport.requests[0][2]["return_full_object"] == "true"
