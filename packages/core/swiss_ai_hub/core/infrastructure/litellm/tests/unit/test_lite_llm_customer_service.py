import json
from collections.abc import Iterator
from unittest.mock import MagicMock, patch

import httpx
import pytest

from swiss_ai_hub.core.auth.identity.tenant_identity import TenantIdentity
from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.infrastructure.litellm.lite_llm_customer_service import LiteLLMCustomerService
from swiss_ai_hub.core.infrastructure.litellm.lite_llm_proxy_settings import LiteLLMProxySettings
from swiss_ai_hub.core.infrastructure.litellm.lite_llm_service import LiteLLMService

pytestmark = pytest.mark.unit

HEADER = LiteLLMCustomerService.CUSTOMER_HEADER


class _RecordingTransport(httpx.MockTransport):
    """Answers each path with its responses in order and records every request with its JSON body."""

    def __init__(self, responses: dict[str, list[httpx.Response]]) -> None:
        self.requests: list[tuple[str, str, dict | None]] = []

        def handler(request: httpx.Request) -> httpx.Response:
            body = json.loads(request.content) if request.content else None
            self.requests.append((request.method, request.url.path, body))
            return responses[request.url.path].pop(0)

        super().__init__(handler)


def _user_in(tenant: TenantIdentity | None) -> UserIdentity:
    return UserIdentity(id="user-1", name="Ada", email="ada@example.com", roles=[], acting_within_tenant=tenant)


def _tenant(tenant_id: str = "tenant-a", name: str = "Tenant A") -> TenantIdentity:
    return TenantIdentity(id=tenant_id, name=name, access_rules=[])


def _customer(alias: str | None) -> httpx.Response:
    return httpx.Response(200, json={"user_id": "tenant-a", "alias": alias})


def _absent() -> httpx.Response:
    return httpx.Response(404, json={"error": {"message": "End User Id=tenant-a does not exist in db"}})


def _already_exists() -> httpx.Response:
    return httpx.Response(400, json={"error": {"message": "Customer already exists, passed user_id=tenant-a."}})


@pytest.fixture(autouse=True)
def _clear_cache() -> Iterator[None]:
    LiteLLMCustomerService._aliases.clear()
    yield
    LiteLLMCustomerService._aliases.clear()


async def _header_for(user: UserIdentity | None, transport: httpx.MockTransport) -> dict[str, str]:
    settings = MagicMock()
    settings.httpx_aclient = httpx.AsyncClient(base_url="http://litellm:4000", transport=transport)
    with patch(
        "swiss_ai_hub.core.infrastructure.litellm.lite_llm_customer_service.LiteLLMProxySettings",
        return_value=settings,
    ):
        return await LiteLLMCustomerService.header_for(user)


@pytest.mark.asyncio
async def test_a_new_tenant_becomes_a_customer_named_after_it() -> None:
    transport = _RecordingTransport({"/customer/info": [_absent()], "/customer/new": [_customer("Tenant A")]})

    header = await _header_for(_user_in(_tenant()), transport)

    assert header == {HEADER: "tenant-a"}
    assert transport.requests[-1] == ("POST", "/customer/new", {"user_id": "tenant-a", "alias": "Tenant A"})


@pytest.mark.asyncio
async def test_a_known_tenant_is_looked_up_once_per_process() -> None:
    transport = _RecordingTransport({"/customer/info": [_customer("Tenant A")]})
    user = _user_in(_tenant())

    await _header_for(user, transport)
    header = await _header_for(user, transport)

    assert header == {HEADER: "tenant-a"}
    assert transport.requests == [("GET", "/customer/info", None)]


@pytest.mark.asyncio
async def test_a_customer_left_without_a_name_gets_the_tenants_name() -> None:
    """The state LiteLLM leaves when a call reached it before the customer was created: a row without an alias."""
    transport = _RecordingTransport({"/customer/info": [_customer(None)], "/customer/update": [_customer("Tenant A")]})

    await _header_for(_user_in(_tenant()), transport)

    assert transport.requests[-1] == ("POST", "/customer/update", {"user_id": "tenant-a", "alias": "Tenant A"})


@pytest.mark.asyncio
async def test_a_renamed_tenant_renames_its_customer() -> None:
    transport = _RecordingTransport(
        {
            "/customer/info": [_customer("Tenant A"), _customer("Tenant A")],
            "/customer/update": [_customer("Tenant A2")],
        }
    )

    await _header_for(_user_in(_tenant()), transport)
    await _header_for(_user_in(_tenant(name="Tenant A2")), transport)

    assert transport.requests[-1] == ("POST", "/customer/update", {"user_id": "tenant-a", "alias": "Tenant A2"})


@pytest.mark.asyncio
async def test_calls_in_two_tenants_are_booked_apart() -> None:
    transport = _RecordingTransport({"/customer/info": [_customer("Tenant A"), _customer("Tenant B")]})

    header_a = await _header_for(_user_in(_tenant()), transport)
    header_b = await _header_for(_user_in(_tenant("tenant-b", "Tenant B")), transport)

    assert (header_a, header_b) == ({HEADER: "tenant-a"}, {HEADER: "tenant-b"})


@pytest.mark.asyncio
@pytest.mark.parametrize("user", [None, _user_in(None)], ids=["no-user", "user-outside-any-tenant"])
async def test_calls_without_a_tenant_name_the_no_tenant_customer(user: UserIdentity | None) -> None:
    """Named rather than left out: the API sends the user's id as `user`, which LiteLLM would book as a customer."""
    transport = _RecordingTransport({})

    header = await _header_for(user, transport)

    assert header == {HEADER: LiteLLMCustomerService.NO_TENANT_CUSTOMER_ID}
    assert transport.requests == []


@pytest.mark.asyncio
async def test_a_customer_created_concurrently_is_accepted() -> None:
    transport = _RecordingTransport(
        {"/customer/info": [_absent(), _customer("Tenant A")], "/customer/new": [_already_exists()]}
    )

    header = await _header_for(_user_in(_tenant()), transport)

    assert header == {HEADER: "tenant-a"}
    assert transport.requests[-1] == ("GET", "/customer/info", None)


@pytest.mark.asyncio
async def test_a_customer_created_concurrently_under_an_old_name_is_renamed() -> None:
    transport = _RecordingTransport(
        {
            "/customer/info": [_absent(), _customer("Old Name")],
            "/customer/new": [_already_exists()],
            "/customer/update": [_customer("Tenant A")],
        }
    )

    await _header_for(_user_in(_tenant()), transport)

    assert transport.requests[-1] == ("POST", "/customer/update", {"user_id": "tenant-a", "alias": "Tenant A"})


@pytest.mark.asyncio
async def test_a_failed_creation_still_books_the_call_and_retries_next_time() -> None:
    """LiteLLM creates the customer itself on the call's spend; only the alias is missing until a later call."""
    transport = _RecordingTransport(
        {"/customer/info": [_absent(), _absent()], "/customer/new": [httpx.Response(500, json={"error": "boom"})]}
    )

    header = await _header_for(_user_in(_tenant()), transport)

    assert header == {HEADER: "tenant-a"}
    assert "tenant-a" not in LiteLLMCustomerService._aliases


@pytest.mark.asyncio
async def test_an_unreachable_litellm_admin_api_still_books_the_call() -> None:
    def refuse(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    header = await _header_for(_user_in(_tenant()), httpx.MockTransport(refuse))

    assert header == {HEADER: "tenant-a"}
    assert "tenant-a" not in LiteLLMCustomerService._aliases


@pytest.mark.asyncio
async def test_the_per_user_openai_client_names_the_customer() -> None:
    """The OpenAI-compatible API, OpenWebUI's chats and the bots all reach LiteLLM through this client."""
    user = _user_in(_tenant())
    LiteLLMService._user_cache[user.id] = "sk-cached"
    LiteLLMCustomerService._aliases["tenant-a"] = "Tenant A"

    with patch(
        "swiss_ai_hub.core.infrastructure.litellm.lite_llm_service.LiteLLMProxySettings",
        return_value=LiteLLMProxySettings(BASE_URL="http://litellm:4000", API_KEY="sk-master"),
    ):
        client = await LiteLLMService.openai_aclient_for_user(user)

    assert client.default_headers[HEADER] == "tenant-a"
    assert client.api_key == "sk-cached"

    LiteLLMService._user_cache.pop(user.id)
    await LiteLLMProxySettings.aclose_pooled_clients()
