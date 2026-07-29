import hashlib
from typing import ClassVar

import httpx
import openai
from cachetools import TTLCache

from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.infrastructure.litellm.lite_llm_proxy_settings import LiteLLMProxySettings


class LiteLLMService:
    _user_cache: ClassVar[TTLCache] = TTLCache(maxsize=1024, ttl=21600)

    @staticmethod
    def generate_key_for_user(user: UserIdentity) -> str:
        sha256_hash = hashlib.sha256()
        sha256_hash.update(user.id.encode("utf-8"))
        return f"sk-{sha256_hash.hexdigest()[:16]}"

    @staticmethod
    async def api_key_for_user(user: UserIdentity) -> str:
        litellm_proxy = LiteLLMProxySettings()

        if user.id in LiteLLMService._user_cache:
            return LiteLLMService._user_cache[user.id]

        api_key = LiteLLMService.generate_key_for_user(user)

        async with litellm_proxy.httpx_aclient as client:
            if await LiteLLMService._create_user_if_absent(client, litellm_proxy, user):
                await LiteLLMService._generate_key(client, user, api_key)

        LiteLLMService._user_cache[user.id] = api_key
        return api_key

    @staticmethod
    async def _create_user_if_absent(
        client: httpx.AsyncClient, litellm_proxy: LiteLLMProxySettings, user: UserIdentity
    ) -> bool:
        """Create the LiteLLM user when missing; return True only when a fresh key must still be generated."""
        user_response = await client.get("/user/info", params={"user_id": user.id})

        # LiteLLM ≥ 1.83 returns 404 only when the user is absent; any 2xx means the user (and its key) exist.
        if user_response.status_code != 404:
            user_response.raise_for_status()
            return False

        new_user_response = await client.post(
            "/user/new",
            json={
                "max_budget": litellm_proxy.USER_MAX_BUDGET,
                "soft_budget": litellm_proxy.USER_SOFT_BUDGET,
                "user_id": user.id,
                "max_parallel_requests": litellm_proxy.USER_MAX_PARALLEL_REQUESTS,
                "tpm_limit": litellm_proxy.USER_TPM_LIMIT,
                "rpm_limit": litellm_proxy.USER_RPM_LIMIT,
                "budget_duration": litellm_proxy.USER_BUDGET_DURATION,
                "blocked": False,
                "user_email": user.email,
                "user_alias": user.name,
                "user_role": "internal_user_viewer",
                "auto_create_key": False,
                "send_invite_email": False,
            },
        )

        # A concurrent first-login request can create the user between the GET and the POST, yielding 409.
        # The concurrent request may not have generated the key yet, so still attempt key generation below.
        if new_user_response.status_code != 409:
            new_user_response.raise_for_status()
        return True

    @staticmethod
    async def _generate_key(client: httpx.AsyncClient, user: UserIdentity, api_key: str) -> None:
        key_response = await client.post(
            "/key/generate",
            json={"key_alias": f"{user.name} - Auto Generated Key", "user_id": user.id, "key": api_key},
        )
        # A concurrent provisioner may have already created this deterministic key; 409 means it exists already.
        if key_response.status_code != 409:
            key_response.raise_for_status()

    @staticmethod
    async def httpx_aclient_for_user(user: UserIdentity) -> httpx.AsyncClient:
        api_key = await LiteLLMService.api_key_for_user(user)
        return httpx.AsyncClient(
            headers={"Authorization": f"Bearer {api_key}"},
            base_url=LiteLLMProxySettings().BASE_URL,
        )

    @staticmethod
    async def openai_aclient_for_user(user: UserIdentity) -> openai.AsyncClient:
        api_key = await LiteLLMService.api_key_for_user(user)
        return openai.AsyncClient(
            api_key=api_key,
            base_url=LiteLLMProxySettings().BASE_URL,
        )
