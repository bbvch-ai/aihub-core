import asyncio
import hashlib
import json
from collections.abc import Callable, Iterator
from unittest.mock import MagicMock, patch

import httpx
import pytest
from pydantic import SecretStr

from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.infrastructure.litellm.lite_llm_proxy_settings import LiteLLMProxySettings
from swiss_ai_hub.core.infrastructure.litellm.lite_llm_service import LiteLLMService

pytestmark = pytest.mark.unit


class _RecordingTransport(httpx.MockTransport):
    """
    MockTransport that records every request path, full URL and JSON body so call expectations can be asserted.

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


def _key_found() -> httpx.Response:
    return httpx.Response(200, json={"key": ["sk-irrelevant"], "info": [{"user_id": "irrelevant"}]})


def _key_missing() -> httpx.Response:
    """What LiteLLM answers for a key that is not live, deleted ones included: a 200 with no info, not a 404."""
    return httpx.Response(200, json={"key": ["sk-irrelevant"], "info": []})


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
        "/v2/key/info": _key_missing(),
        "/user/info": httpx.Response(404, json={"error": "not found"}),
        "/user/list": httpx.Response(200, json={"users": email_holders}),
        "/user/update": httpx.Response(200, json={}),
        "/user/new": httpx.Response(200, json={}),
        "/key/generate": httpx.Response(200, json={"key": "sk-irrelevant"}),
    }


def _settings(master_key: str | None = "sk-master") -> LiteLLMProxySettings:
    return LiteLLMProxySettings(BASE_URL="http://litellm:4000", API_KEY=master_key)


@pytest.fixture(autouse=True)
def _clear_cache() -> Iterator[None]:
    """Only the key cache; the pools belong to `_no_pool_residue`, which asserts rather than clears."""
    LiteLLMService._user_cache.clear()
    yield
    LiteLLMService._user_cache.clear()


def _patched_settings(transport: _RecordingTransport) -> MagicMock:
    settings = MagicMock()
    settings.API_KEY = SecretStr("sk-master")
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
    user = _user("existing-user")
    transport = _RecordingTransport(
        {"/user/info": httpx.Response(200, json={"user_id": "existing-user"}), "/v2/key/info": _key_found()}
    )

    key = await _run(transport, user)

    assert key == LiteLLMService.generate_key_for_user(user, _settings())
    assert transport.requests == [("GET", "/user/info"), ("POST", "/v2/key/info")]


@pytest.mark.asyncio
async def test_user_without_a_key_recovers() -> None:
    """The state a key generation failing after user creation left behind, which no request used to repair."""
    user = _user("stuck-user")
    transport = _RecordingTransport(
        _provisioning_responses(email_holders=[])
        | {"/user/info": httpx.Response(200, json={"user_id": "stuck-user", "keys": []})}
    )

    key = await _run(transport, user)

    assert key == LiteLLMService.generate_key_for_user(user, _settings())
    assert transport.requests == [("GET", "/user/info"), ("POST", "/v2/key/info"), ("POST", "/key/generate")]


@pytest.mark.asyncio
async def test_key_without_a_user_row_gets_its_row() -> None:
    """
    A user created while its email was still held by a stale account got its key but no row, and so no budget
    or rate limits; an existing key must not stop the row from being created.
    """
    user = _user("key-without-row")
    transport = _RecordingTransport(_provisioning_responses(email_holders=[]) | {"/v2/key/info": _key_found()})

    key = await _run(transport, user)

    assert key == LiteLLMService.generate_key_for_user(user, _settings())
    assert transport.requests == [
        ("GET", "/user/info"),
        ("GET", "/user/list"),
        ("POST", "/user/new"),
        ("POST", "/v2/key/info"),
    ]


@pytest.mark.asyncio
async def test_absent_user_is_created_with_a_key() -> None:
    user = _user("new-user")
    transport = _RecordingTransport(_provisioning_responses(email_holders=[]))

    key = await _run(transport, user)

    assert key == LiteLLMService.generate_key_for_user(user, _settings())
    assert transport.requests == [
        ("GET", "/user/info"),
        ("GET", "/user/list"),
        ("POST", "/user/new"),
        ("POST", "/v2/key/info"),
        ("POST", "/key/generate"),
    ]


@pytest.mark.asyncio
async def test_user_new_conflict_still_generates_the_key() -> None:
    user = _user("racing-user")
    transport = _RecordingTransport(
        _provisioning_responses(email_holders=[])
        | {"/user/new": httpx.Response(409, json={"error": "User with id racing-user already exists"})}
    )

    key = await _run(transport, user)

    assert key == LiteLLMService.generate_key_for_user(user, _settings())
    assert transport.requests == [
        ("GET", "/user/info"),
        ("GET", "/user/list"),
        ("POST", "/user/new"),
        ("POST", "/v2/key/info"),
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
        | {"/v2/key/info": [_key_missing(), _key_found()], "/key/generate": rejection()}
    )

    key = await _run(transport, user)

    assert key == LiteLLMService.generate_key_for_user(user, _settings())
    assert transport.requests == [
        ("GET", "/user/info"),
        ("GET", "/user/list"),
        ("POST", "/user/new"),
        ("POST", "/v2/key/info"),
        ("POST", "/key/generate"),
        ("POST", "/v2/key/info"),
    ]


@pytest.mark.asyncio
async def test_key_generate_rejection_propagates_without_caching_when_the_key_is_missing() -> None:
    user = _user("rejected-user")
    transport = _RecordingTransport(
        _provisioning_responses(email_holders=[])
        | {"/v2/key/info": [_key_missing(), _key_missing()], "/key/generate": _duplicate_alias()}
    )

    with pytest.raises(httpx.HTTPStatusError) as error:
        await _run(transport, user)

    assert error.value.response.status_code == 400
    assert transport.requests[-2:] == [("POST", "/key/generate"), ("POST", "/v2/key/info")]
    assert user.id not in LiteLLMService._user_cache


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
        ("POST", "/v2/key/info"),
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
async def test_key_carries_the_generation_of_its_master_key() -> None:
    """The user's earlier key keeps its alias, and LiteLLM would refuse a second key under it."""
    user = _user("generation-user")
    transport = _RecordingTransport(_provisioning_responses(email_holders=[]))

    await _run(transport, user)

    generation = LiteLLMService.key_generation(_settings())
    assert transport.bodies["/key/generate"]["key_alias"] == (
        f"Ada Lovelace (generation-user) - Auto Generated Key {generation}"
    )
    assert transport.bodies["/key/generate"]["metadata"] == {"swiss_ai_hub_key_generation": generation}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "responses",
    [
        _provisioning_responses(email_holders=[]),
        {"/user/info": httpx.Response(200, json={"user_id": "url-user"}), "/v2/key/info": _key_found()},
    ],
    ids=["new-user", "existing-user"],
)
async def test_no_request_carries_the_key_in_its_url(responses: dict[str, httpx.Response]) -> None:
    """URLs are written to logs and traces, which are kept longer and read by more people than the key itself."""
    user = _user("url-user")
    transport = _RecordingTransport(responses)

    key = await _run(transport, user)

    assert [url for url in transport.urls if key in url] == []
    assert transport.bodies["/v2/key/info"] == {"keys": [key]}


def test_the_key_follows_from_the_user_and_the_master_key_together() -> None:
    """
    One pair must give one key in every process, or concurrent first requests mint two. Another master key must give
    another key and generation, or the key would follow from the user id alone.
    """
    user = _user("same-user")
    one_process, another_process = _settings(), _settings()

    assert LiteLLMService.generate_key_for_user(user, one_process) == LiteLLMService.generate_key_for_user(
        user, another_process
    )
    assert LiteLLMService.generate_key_for_user(user, _settings("sk-first")) != LiteLLMService.generate_key_for_user(
        user, _settings("sk-second")
    )
    assert LiteLLMService.key_generation(_settings("sk-first")) != LiteLLMService.key_generation(_settings("sk-second"))


def test_the_key_no_longer_follows_from_the_user_id_alone() -> None:
    """The derivation before, which anyone who knew a user's id could repeat."""
    user = _user("known-id")

    assert LiteLLMService.generate_key_for_user(user, _settings()) != (
        f"sk-{hashlib.sha256(user.id.encode('utf-8')).hexdigest()[:16]}"
    )


def test_keys_are_not_derived_without_a_master_key() -> None:
    user, without_master_key = _user("any-user"), _settings(None)

    with pytest.raises(ValueError, match="LITE_LLM_PROXY_API_KEY"):
        LiteLLMService.generate_key_for_user(user, without_master_key)


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
        {
            "/user/info": httpx.Response(200, json={"user_id": "erroring-user"}),
            "/v2/key/info": httpx.Response(500, json={"error": "boom"}),
        },
    ],
    ids=["user-info", "key-info"],
)
async def test_server_error_propagates_without_caching(responses: dict[str, httpx.Response]) -> None:
    user = _user("erroring-user")
    transport = _RecordingTransport(responses)

    with pytest.raises(httpx.HTTPStatusError):
        await _run(transport, user)

    assert user.id not in LiteLLMService._user_cache
