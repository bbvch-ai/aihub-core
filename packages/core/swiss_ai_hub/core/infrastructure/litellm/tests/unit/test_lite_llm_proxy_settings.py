import asyncio
from collections.abc import Awaitable, Callable
from unittest.mock import patch

import httpx
import pytest

from swiss_ai_hub.core.infrastructure.litellm.lite_llm_proxy_settings import LiteLLMProxySettings

pytestmark = pytest.mark.unit


def _settings(base_url: str = "http://litellm:4000") -> LiteLLMProxySettings:
    return LiteLLMProxySettings(BASE_URL=base_url, API_KEY="sk-master")


def _release_pools() -> None:
    """The sync entry point for tests with no running loop; `aclose_pooled_clients` owns both pools."""
    asyncio.run(LiteLLMProxySettings.aclose_pooled_clients())


def test_sync_client_is_reused_across_accesses_and_instances() -> None:
    first_instance, second_instance = _settings(), _settings()

    assert first_instance.httpx_client is second_instance.httpx_client

    _release_pools()


@pytest.mark.asyncio
async def test_async_clients_are_reused_across_accesses_and_instances() -> None:
    first_instance, second_instance = _settings(), _settings()

    assert first_instance.httpx_aclient is second_instance.httpx_aclient
    assert first_instance.openai_aclient is second_instance.openai_aclient

    await LiteLLMProxySettings.aclose_pooled_clients()


@pytest.mark.asyncio
async def test_distinct_base_urls_get_distinct_clients() -> None:
    assert _settings("http://a:4000").httpx_aclient is not _settings("http://b:4000").httpx_aclient
    assert _settings().httpx_aclient is not _settings().openai_aclient

    await LiteLLMProxySettings.aclose_pooled_clients()


@pytest.mark.asyncio
async def test_closing_the_pools_closes_every_client() -> None:
    httpx_aclient, openai_aclient, sync_client = (
        _settings().httpx_aclient,
        _settings().openai_aclient,
        _settings().httpx_client,
    )

    await LiteLLMProxySettings.aclose_pooled_clients()

    # Read raw, the OpenAI SDK's `is_closed` is a bound method and so truthy even while open.
    assert LiteLLMProxySettings.client_is_closed(httpx_aclient)
    assert LiteLLMProxySettings.client_is_closed(openai_aclient)
    assert LiteLLMProxySettings.client_is_closed(sync_client)


@pytest.mark.asyncio
async def test_an_open_openai_client_is_not_reported_as_closed() -> None:
    """`openai.AsyncClient.is_closed` is a method, so the raw attribute is truthy on an open client."""
    assert not LiteLLMProxySettings.client_is_closed(_settings().openai_aclient)

    await LiteLLMProxySettings.aclose_pooled_clients()


@pytest.mark.asyncio
async def test_pools_rebuild_after_being_closed() -> None:
    """A process that starts a second app on the same loop must not inherit the first app's closed clients."""
    first = _settings().httpx_aclient

    await LiteLLMProxySettings.aclose_pooled_clients()

    second = _settings().httpx_aclient
    assert second is not first
    assert not second.is_closed

    await LiteLLMProxySettings.aclose_pooled_clients()


@pytest.mark.asyncio
async def test_a_client_closed_by_its_caller_is_replaced_rather_than_handed_out() -> None:
    """Only a docstring stops a caller closing a pooled client; a poisoned entry must not outlive it."""
    closed_by_caller = _settings().httpx_aclient
    await closed_by_caller.aclose()

    replacement = _settings().httpx_aclient

    assert replacement is not closed_by_caller
    assert not replacement.is_closed

    await LiteLLMProxySettings.aclose_pooled_clients()


@pytest.mark.asyncio
async def test_closing_a_handed_out_client_does_not_break_the_next_caller() -> None:
    """
    `async with client:` closes on exit without going through `aclose`, poisoning the pool the same way.

    Asserted by making a real request through the next handed-out client rather than reading `is_closed`,
    since the symptom callers actually hit is `RuntimeError: Cannot send a request, as the client has been
    closed` raised from `send` — for the rest of the process, on every later access.
    """
    async with _settings().httpx_aclient:
        pass

    with patch.object(httpx.AsyncHTTPTransport, "handle_async_request", new=_respond_with(httpx.Response(200))):
        response = await _settings().httpx_aclient.get("/health")

    assert response.status_code == 200

    await LiteLLMProxySettings.aclose_pooled_clients()


def _respond_with(response: httpx.Response) -> Callable[..., Awaitable[httpx.Response]]:
    async def handle_async_request(*_args: object, **_kwargs: object) -> httpx.Response:
        return response

    return handle_async_request


def test_a_sync_client_closed_by_its_caller_is_replaced_rather_than_handed_out() -> None:
    closed_by_caller = _settings().httpx_client
    closed_by_caller.close()

    replacement = _settings().httpx_client

    assert replacement is not closed_by_caller
    assert not replacement.is_closed

    _release_pools()


def test_each_event_loop_gets_its_own_client() -> None:
    """A client's pooled connections belong to the loop that opened them, so they must not cross loops."""
    first = asyncio.run(_resolve_and_release_aclient())
    second = asyncio.run(_resolve_and_release_aclient())

    assert first is not second


async def _resolve_and_release_aclient() -> object:
    """Releases inside the loop that pooled it: the weak key only drops once that loop is collected."""
    client = _settings().httpx_aclient
    await LiteLLMProxySettings.aclose_pooled_clients()
    return client
