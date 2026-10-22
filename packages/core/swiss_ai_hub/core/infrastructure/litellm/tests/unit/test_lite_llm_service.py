import asyncio
import hashlib
import json
from collections.abc import Callable, Iterator
from unittest.mock import MagicMock, patch

import httpx
import pytest

from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.infrastructure.litellm.lite_llm_proxy_settings import LiteLLMProxySettings
from swiss_ai_hub.core.infrastructure.litellm.lite_llm_service import LiteLLMService

pytestmark = pytest.mark.unit


class _RecordingTransport(httpx.MockTransport):
    """
    MockTransport that records every request path, URL and JSON body so call expectations can be asserted.

    A path mapped to a list answers with its responses in order, for a path asked twice with different outcomes.
    """

    def __init__(self, responses: dict[str, httpx.Response | list[httpx.Response]]) -> None:
        self.requests: list[tuple[str, str]] = []
        self.urls: list[str] = []
        self.bodies: dict[str, dict] = {}

        def handler(request: httpx.Request) -> httpx.Response:
            self.requests.append((request.method, request.url.path))
            self.urls.append(str(request.url))
            if request.content:
                self.bodies[request.url.path] = json.loads(request.content)
            response = responses[request.url.path]
            return response.pop(0) if isinstance(response, list) else response

        super().__init__(handler)


def _user(user_id: str, email: str = "ada@example.com") -> UserIdentity:
    return UserIdentity(id=user_id, name="Ada Lovelace", email=email, roles=[])


def _user_row(*api_keys: str) -> httpx.Response:
    """The /user/info answer for an existing user, listing its live keys by their stored hash."""
    keys = [{"token": hashlib.sha256(api_key.encode()).hexdigest()} for api_key in api_keys]
    return httpx.Response(200, json={"user_id": "irrelevant", "keys": keys})


def _user_missing() -> httpx.Response:
    return httpx.Response(404, json={"error": "not found"})


def _duplicate_alias() -> httpx.Response:
    """What LiteLLM answers for a duplicate alias: a 400, not a 409."""
    return httpx.Response(
        400,
        json={
            "error": {"message": "Key with alias 'x' already exists. Unique key aliases across all keys are required."}
        },
    )


def _provisioning_responses(email_holders: list[dict]) -> dict[str, httpx.Response | list[httpx.Response]]:
    return {
        "/user/info": [_user_missing(), _user_row()],
        "/user/list": httpx.Response(200, json={"users": email_holders}),
        "/user/update": httpx.Response(200, json={}),
        "/user/new": httpx.Response(200, json={}),
        "/key/generate": httpx.Response(200, json={"key": "sk-irrelevant"}),
    }


def _settings() -> LiteLLMProxySettings:
    return LiteLLMProxySettings(BASE_URL="http://litellm:4000", API_KEY="sk-master")


@pytest.fixture(autouse=True)
def _clear_cache() -> Iterator[None]:
    """Only the key cache; the pools belong to `_no_pool_residue`, which asserts rather than clears."""
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
async def test_existing_key_is_returned_without_provisioning() -> None:
    """Keys issued under an earlier alias format resolve the same way, so they need no migration."""
    user = _user("existing-user")
    transport = _RecordingTransport({"/user/info": _user_row(LiteLLMService.generate_key_for_user(user))})

    key = await _run(transport, user)

    assert key == LiteLLMService.generate_key_for_user(user)
    assert transport.requests == [("GET", "/user/info")]


@pytest.mark.asyncio
async def test_user_without_a_key_recovers() -> None:
    """
    The state a key generation failing after user creation left behind, which no request used to repair. A key
    deleted in LiteLLM looks the same here: it is no longer among the live keys, so it is created again.
    """
    user = _user("stuck-user")
    transport = _RecordingTransport(_provisioning_responses(email_holders=[]) | {"/user/info": _user_row("sk-other")})

    key = await _run(transport, user)

    assert key == LiteLLMService.generate_key_for_user(user)
    assert transport.requests == [("GET", "/user/info"), ("POST", "/key/generate")]


@pytest.mark.asyncio
async def test_absent_user_is_created_with_a_key() -> None:
    user = _user("new-user")
    transport = _RecordingTransport(_provisioning_responses(email_holders=[]))

    key = await _run(transport, user)

    assert key == LiteLLMService.generate_key_for_user(user)
    assert transport.requests == [
        ("GET", "/user/info"),
        ("GET", "/user/list"),
        ("POST", "/user/new"),
        ("GET", "/user/info"),
        ("POST", "/key/generate"),
    ]


@pytest.mark.asyncio
async def test_key_without_a_user_row_gets_its_row() -> None:
    """
    A user created while its email was still held by a stale account got its key but no row, and so no budget
    or rate limits; an existing key must not stop the row from being created.
    """
    user = _user("key-without-row")
    transport = _RecordingTransport(
        _provisioning_responses(email_holders=[])
        | {"/user/info": [_user_missing(), _user_row(LiteLLMService.generate_key_for_user(user))]}
    )

    key = await _run(transport, user)

    assert key == LiteLLMService.generate_key_for_user(user)
    assert transport.requests == [
        ("GET", "/user/info"),
        ("GET", "/user/list"),
        ("POST", "/user/new"),
        ("GET", "/user/info"),
    ]


@pytest.mark.asyncio
async def test_user_new_conflict_still_generates_the_key() -> None:
    user = _user("racing-user")
    transport = _RecordingTransport(
        _provisioning_responses(email_holders=[])
        | {"/user/new": httpx.Response(409, json={"error": "User with id racing-user already exists"})}
    )

    key = await _run(transport, user)

    assert key == LiteLLMService.generate_key_for_user(user)
    assert transport.requests == [
        ("GET", "/user/info"),
        ("GET", "/user/list"),
        ("POST", "/user/new"),
        ("GET", "/user/info"),
        ("POST", "/key/generate"),
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "rejection",
    [_duplicate_alias, lambda: httpx.Response(409, json={"error": "key already exists"})],
    ids=["duplicate-alias", "conflict"],
)
async def test_key_generate_rejection_is_success_when_the_key_exists(rejection: Callable[[], httpx.Response]) -> None:
    """A concurrent first request created the same deterministic key in between."""
    user = _user("racing-key-user")
    transport = _RecordingTransport(
        _provisioning_responses(email_holders=[])
        | {
            "/user/info": [_user_row(), _user_row(LiteLLMService.generate_key_for_user(user))],
            "/key/generate": rejection(),
        }
    )

    key = await _run(transport, user)

    assert key == LiteLLMService.generate_key_for_user(user)
    assert transport.requests == [("GET", "/user/info"), ("POST", "/key/generate"), ("GET", "/user/info")]


@pytest.mark.asyncio
async def test_key_generate_rejection_propagates_without_caching_when_the_key_is_missing() -> None:
    user = _user("rejected-user")
    transport = _RecordingTransport(
        _provisioning_responses(email_holders=[])
        | {"/user/info": [_user_row(), _user_row()], "/key/generate": _duplicate_alias()}
    )

    with pytest.raises(httpx.HTTPStatusError) as error:
        await _run(transport, user)

    assert error.value.response.status_code == 400
    assert transport.requests == [("GET", "/user/info"), ("POST", "/key/generate"), ("GET", "/user/info")]
    assert user.id not in LiteLLMService._user_cache


@pytest.mark.asyncio
async def test_the_key_never_appears_in_a_url() -> None:
    """Access logs in front of LiteLLM and our own traces record URLs verbatim; the key travels only in bodies."""
    user = _user("url-user")
    api_key = LiteLLMService.generate_key_for_user(user)
    transport = _RecordingTransport(_provisioning_responses(email_holders=[]))

    await _run(transport, user)

    assert not [url for url in transport.urls if api_key in url or hashlib.sha256(api_key.encode()).hexdigest() in url]


@pytest.mark.asyncio
async def test_email_held_by_a_deleted_account_is_released_before_the_user_is_created() -> None:
    """Without the release, /user/new answers 409 for the email and the user is left without a row or budget."""
    user = _user("recreated-account")
    transport = _RecordingTransport(
        _provisioning_responses(email_holders=[{"user_id": "deleted-account", "user_email": "Ada@Example.com"}])
    )

    await _run(transport, user)

    assert transport.requests == [
        ("GET", "/user/info"),
        ("GET", "/user/list"),
        ("POST", "/user/update"),
        ("POST", "/user/new"),
        ("GET", "/user/info"),
        ("POST", "/key/generate"),
    ]
    assert transport.bodies["/user/update"] == {
        "user_id": "deleted-account",
        "user_email": "ada@example.com#released-deleted-account",
    }
    assert transport.bodies["/user/new"]["user_email"] == "ada@example.com"


@pytest.mark.asyncio
async def test_own_row_and_substring_email_matches_are_left_alone() -> None:
    """The own row is a concurrent first login; the others only contain the email, as LiteLLM's filter allows."""
    user = _user("racing-user")
    transport = _RecordingTransport(
        _provisioning_responses(
            email_holders=[
                {"user_id": "racing-user", "user_email": "ada@example.com"},
                {"user_id": "someone-else", "user_email": "nada@example.com"},
                {"user_id": "already-released", "user_email": "ada@example.com#released-already-released"},
            ]
        )
    )

    await _run(transport, user)

    assert ("POST", "/user/update") not in transport.requests


@pytest.mark.asyncio
async def test_user_without_email_skips_the_email_lookup() -> None:
    user = _user("service-account", email="")
    transport = _RecordingTransport(_provisioning_responses(email_holders=[]))

    await _run(transport, user)

    assert ("GET", "/user/list") not in transport.requests


@pytest.mark.asyncio
async def test_key_alias_is_unique_for_users_sharing_a_display_name() -> None:
    """LiteLLM rejects a second key with an existing alias, so the alias cannot rest on the display name alone."""
    aliases = []
    for user in (_user("first-ada"), _user("second-ada")):
        transport = _RecordingTransport(_provisioning_responses(email_holders=[]))
        await _run(transport, user)
        aliases.append(transport.bodies["/key/generate"]["key_alias"])

    assert aliases[0] != aliases[1]


@pytest.mark.asyncio
async def test_per_user_openai_clients_share_one_connection_pool() -> None:
    """
    The per-user client dimension is unbounded — no maxsize, no TTL, no eviction — so it must not be a
    dimension of the pool. `with_options` re-uses the shared client's httpx client, costing no extra pool.
    """
    user, other_user = _user("pooled-client-user"), _user("other-user")
    LiteLLMService._user_cache[user.id] = "sk-cached"
    LiteLLMService._user_cache[other_user.id] = "sk-other"

    with patch(
        "swiss_ai_hub.core.infrastructure.litellm.lite_llm_service.LiteLLMProxySettings",
        return_value=_settings(),
    ):
        client, other_client = (
            await LiteLLMService.openai_aclient_for_user(user),
            await LiteLLMService.openai_aclient_for_user(other_user),
        )

        assert client.api_key == "sk-cached"
        assert other_client.api_key == "sk-other"
        assert client._client is other_client._client
        assert len(LiteLLMProxySettings._async_clients[asyncio.get_running_loop()]) == 1

    await LiteLLMProxySettings.aclose_pooled_clients()


@pytest.mark.asyncio
async def test_pool_size_is_independent_of_user_count(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    User count must not be a dimension of the pool at all, which is a stronger claim than any bound on it:
    asserting a `maxsize`/TTL would concede the dimension exists and only cap how far it grows.

    Settings come from the environment rather than a patched class, so the real `pooled_async_client` runs —
    patching the class out replaces the pool itself, and the growth this guards against would go unseen.
    The pool is deliberately not cleared between rounds, so the last one resolves the 551st distinct user
    against the same single entry.
    """
    monkeypatch.setenv("LITE_LLM_PROXY_BASE_URL", "http://litellm:4000")
    monkeypatch.setenv("LITE_LLM_PROXY_API_KEY", "sk-master")

    pool_sizes = [await _pool_size_after_resolving_clients_for(user_count) for user_count in (1, 50, 500)]

    assert pool_sizes == [1, 1, 1]

    await LiteLLMProxySettings.aclose_pooled_clients()


async def _pool_size_after_resolving_clients_for(user_count: int) -> int:
    for index in range(user_count):
        user = _user(f"user-{user_count}-{index}")
        LiteLLMService._user_cache[user.id] = f"sk-{user_count}-{index}"
        await LiteLLMService.openai_aclient_for_user(user)

    return len(LiteLLMProxySettings._async_clients[asyncio.get_running_loop()])


@pytest.mark.asyncio
async def test_authorization_header_carries_the_users_key() -> None:
    user = _user("header-user")
    LiteLLMService._user_cache[user.id] = "sk-cached"

    assert await LiteLLMService.authorization_header_for_user(user) == {"Authorization": "Bearer sk-cached"}


@pytest.mark.asyncio
async def test_the_users_key_overrides_the_shared_clients_master_key() -> None:
    """The shared client authenticates as the master key, so the per-request header has to win."""
    user = _user("overriding-user")
    LiteLLMService._user_cache[user.id] = "sk-cached"
    shared_client = _settings().httpx_aclient

    request = shared_client.build_request(
        "GET", "/v1/model/info", headers=await LiteLLMService.authorization_header_for_user(user)
    )

    assert request.headers["authorization"] == "Bearer sk-cached"

    await LiteLLMProxySettings.aclose_pooled_clients()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "responses",
    [
        {"/user/info": httpx.Response(500, json={"error": "boom"})},
        {"/user/info": _user_missing(), "/user/list": httpx.Response(500, json={"error": "boom"})},
    ],
    ids=["user-info", "user-list"],
)
async def test_server_error_propagates_without_caching(responses: dict[str, httpx.Response]) -> None:
    user = _user("erroring-user")
    transport = _RecordingTransport(responses)

    with pytest.raises(httpx.HTTPStatusError):
        await _run(transport, user)

    assert user.id not in LiteLLMService._user_cache
