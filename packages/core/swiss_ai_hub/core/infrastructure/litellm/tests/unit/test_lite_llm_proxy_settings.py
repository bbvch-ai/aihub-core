import asyncio
from collections.abc import Iterator

import pytest

from swiss_ai_hub.core.infrastructure.litellm.lite_llm_proxy_settings import LiteLLMProxySettings

pytestmark = pytest.mark.unit


def _settings(base_url: str = "http://litellm:4000") -> LiteLLMProxySettings:
    return LiteLLMProxySettings(BASE_URL=base_url, API_KEY="sk-master")


@pytest.fixture(autouse=True)
def _clear_pools() -> Iterator[None]:
    LiteLLMProxySettings._sync_clients.clear()
    LiteLLMProxySettings._async_clients.clear()
    yield
    LiteLLMProxySettings._sync_clients.clear()
    LiteLLMProxySettings._async_clients.clear()


def test_sync_client_is_reused_across_accesses_and_instances() -> None:
    assert _settings().httpx_client is _settings().httpx_client


@pytest.mark.asyncio
async def test_async_clients_are_reused_across_accesses_and_instances() -> None:
    assert _settings().httpx_aclient is _settings().httpx_aclient
    assert _settings().openai_aclient is _settings().openai_aclient


@pytest.mark.asyncio
async def test_distinct_base_urls_get_distinct_clients() -> None:
    assert _settings("http://a:4000").httpx_aclient is not _settings("http://b:4000").httpx_aclient
    assert _settings().httpx_aclient is not _settings().openai_aclient


@pytest.mark.asyncio
async def test_closing_the_pools_closes_every_client() -> None:
    httpx_aclient, openai_aclient, sync_client = (
        _settings().httpx_aclient,
        _settings().openai_aclient,
        _settings().httpx_client,
    )

    await LiteLLMProxySettings.aclose_pooled_clients()

    assert httpx_aclient.is_closed
    assert openai_aclient.is_closed
    assert sync_client.is_closed


@pytest.mark.asyncio
async def test_pools_rebuild_after_being_closed() -> None:
    """A process that starts a second app on the same loop must not inherit the first app's closed clients."""
    first = _settings().httpx_aclient

    await LiteLLMProxySettings.aclose_pooled_clients()

    second = _settings().httpx_aclient
    assert second is not first
    assert not second.is_closed


def test_each_event_loop_gets_its_own_client() -> None:
    """A client's pooled connections belong to the loop that opened them, so they must not cross loops."""
    first = asyncio.run(_resolve_aclient())
    second = asyncio.run(_resolve_aclient())

    assert first is not second


async def _resolve_aclient() -> object:
    return _settings().httpx_aclient
