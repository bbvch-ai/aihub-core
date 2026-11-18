"""Provision a throwaway user's key through the real LiteLLM proxy and remove the user afterwards.

Run on every LiteLLM upgrade, with the dev docker stack up (LiteLLM healthy) and the master key in .env:
    uv run pytest -m integration \
        swiss_ai_hub/core/infrastructure/litellm/tests/integration/test_user_key_provisioning.py -v

Marked `integration` so the default `make test` (-m unit) skips it.
"""

import uuid
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio

from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.infrastructure.litellm.lite_llm_proxy_settings import LiteLLMProxySettings
from swiss_ai_hub.core.infrastructure.litellm.lite_llm_service import LiteLLMService

pytestmark = pytest.mark.integration


@pytest_asyncio.fixture
async def throwaway_user() -> AsyncIterator[UserIdentity]:
    """No email, so provisioning never looks at, or releases the email of, a real user."""
    user = UserIdentity(
        id=f"swiss-ai-hub-key-test-{uuid.uuid4().hex}", name="Key Provisioning Test", email="", roles=[]
    )
    yield user
    LiteLLMService._user_cache.pop(user.id, None)
    response = await LiteLLMProxySettings().httpx_aclient.post("/user/delete", json={"user_ids": [user.id]})
    response.raise_for_status()
    await LiteLLMProxySettings.aclose_pooled_clients()


@pytest.mark.asyncio
async def test_an_existing_key_is_found_again_and_works(throwaway_user: UserIdentity) -> None:
    """
    The lookup relies on what no unit test sees: an endpoint outside LiteLLM's published schema, which hashes the
    key itself. Should an upgrade change either, the second resolution misses the key and fails on its duplicate
    alias, as would every user's first request after a restart.
    """
    key = await LiteLLMService.api_key_for_user(throwaway_user)
    LiteLLMService._user_cache.pop(throwaway_user.id)

    assert await LiteLLMService.api_key_for_user(throwaway_user) == key
    await _assert_key_authenticates(key)


@pytest.mark.asyncio
async def test_a_deleted_key_is_minted_again(throwaway_user: UserIdentity) -> None:
    key = await LiteLLMService.api_key_for_user(throwaway_user)
    response = await LiteLLMProxySettings().httpx_aclient.post("/key/delete", json={"keys": [key]})
    response.raise_for_status()
    LiteLLMService._user_cache.pop(throwaway_user.id)

    assert await LiteLLMService.api_key_for_user(throwaway_user) == key
    await _assert_key_authenticates(key)


async def _assert_key_authenticates(key: str) -> None:
    response = await LiteLLMProxySettings().httpx_aclient.get("/v1/models", headers={"Authorization": f"Bearer {key}"})
    assert response.status_code == 200, response.text
