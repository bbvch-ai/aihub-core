import hashlib
from typing import ClassVar

import httpx
import openai
from cachetools import TTLCache

from swiss_ai_hub.core.auth.identity.UserIdentity import UserIdentity
from swiss_ai_hub.core.infrastructure.litellm.LiteLLMProxySettings import LiteLLMProxySettings


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

        client = litellm_proxy.httpx_aclient
        key_alias = f"{user.name} - Auto Generated Key"

        user_response = await client.get("/user/info", params={"user_id": user.id})

        user_response.raise_for_status()
        user_data = user_response.json()
        user_exists = user_data.get("user_info", {}).get("user_alias")

        if user_exists:
            return LiteLLMService.generate_key_for_user(user)

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
        new_user_response.raise_for_status()

        generated_key = await client.post(
            "/key/generate",
            json={"key_alias": key_alias, "user_id": user.id, "key": LiteLLMService.generate_key_for_user(user)},
        )
        generated_key.raise_for_status()
        data = generated_key.json()
        key = data["key"]
        LiteLLMService._user_cache[user.id] = key
        return key

    @staticmethod
    async def httpx_client_for_user(user: UserIdentity) -> httpx.Client:
        api_key = await LiteLLMService.api_key_for_user(user)
        return httpx.Client(
            headers={"Authorization": f"Bearer {api_key}"},
            base_url=LiteLLMProxySettings().BASE_URL,
        )

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
