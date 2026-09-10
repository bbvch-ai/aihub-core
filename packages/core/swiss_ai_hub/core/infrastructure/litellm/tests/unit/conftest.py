from collections.abc import AsyncIterator

import pytest_asyncio

from swiss_ai_hub.core.infrastructure.litellm.lite_llm_proxy_settings import LiteLLMProxySettings


@pytest_asyncio.fixture(autouse=True)
async def _no_pool_residue() -> AsyncIterator[None]:
    """
    Fail the test that leaks a pooled client rather than the unrelated test it would otherwise break.

    The pools are process-wide `ClassVar`s, so anything left behind is visible to every later test, and
    under `pytest-randomly` the victim differs run to run. Tests release through `aclose_pooled_clients`,
    which makes the production teardown path incidental coverage of every test here.

    Async, because `_async_clients` is keyed weakly by event loop: a sync fixture tears down after
    pytest-asyncio has collected the test's loop, by which point the entry has evaporated and the
    assertion cannot fail. This runs inside that loop instead, while the residue is still reachable.

    Setup still clears: `LiteLLMProxySettings` is pooled from `lite_llm_base` and `openwebui_provisioner`
    too, and residue from a test file outside this fixture would otherwise be charged to whichever test
    here happened to run first.
    """
    LiteLLMProxySettings._sync_clients.clear()
    LiteLLMProxySettings._async_clients.clear()

    yield

    assert not LiteLLMProxySettings._sync_clients, "test leaked a sync client into the pool"
    assert not LiteLLMProxySettings._async_clients, "test leaked an async client into the pool"
