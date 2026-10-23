import hashlib
from typing import Any, ClassVar

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

        client = litellm_proxy.httpx_aclient
        await LiteLLMService._create_user_if_absent(client, litellm_proxy, user)
        if not await LiteLLMService._key_exists(client, api_key):
            await LiteLLMService._generate_key(client, user, api_key)

        LiteLLMService._user_cache[user.id] = api_key
        return api_key

    @staticmethod
    async def _key_exists(client: httpx.AsyncClient, api_key: str) -> bool:
        """
        The user row and its key are created by separate calls, and either can fail after the other succeeded, so
        each is checked on its own rather than inferred from the other: a key without its row carries no budget or
        rate limits, and a row without its key fails every request.

        From LiteLLM v1.106 on, a deleted key still answers 200, from an archive, with status "deleted".
        """
        key_response = await client.get("/key/info", params={"key": api_key})
        if key_response.status_code == 404:
            return False
        key_response.raise_for_status()
        return key_response.json()["info"].get("status") != "deleted"

    @staticmethod
    async def _create_user_if_absent(
        client: httpx.AsyncClient, litellm_proxy: LiteLLMProxySettings, user: UserIdentity
    ) -> None:
        user_response = await client.get("/user/info", params={"user_id": user.id})

        # LiteLLM ≥ 1.83 returns 404 only when the user is absent.
        if user_response.status_code != 404:
            user_response.raise_for_status()
            return

        await LiteLLMService._release_email_from_stale_users(client, user)

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
        if new_user_response.status_code != 409:
            new_user_response.raise_for_status()

    @staticmethod
    async def _release_email_from_stale_users(client: httpx.AsyncClient, user: UserIdentity) -> None:
        """
        LiteLLM answers a duplicate email with the 409 the race handling swallows, leaving the user without a row
        and so without budgets. Keycloak allows one account per email, so any other holder is a deleted or
        re-emailed account; renaming rather than deleting it keeps its key working and its spend.
        """
        if not user.email:
            return

        # The filter is a case-insensitive substring match, so holders are narrowed to exact matches below.
        users_response = await client.get("/user/list", params={"user_email": user.email, "page_size": 100})
        users_response.raise_for_status()

        for holder in users_response.json()["users"]:
            if LiteLLMService._is_stale_holder_of_email(holder, user):
                update_response = await client.post(
                    "/user/update",
                    json={"user_id": holder["user_id"], "user_email": f"{user.email}#released-{holder['user_id']}"},
                )
                update_response.raise_for_status()

    @staticmethod
    def _is_stale_holder_of_email(holder: dict[str, Any], user: UserIdentity) -> bool:
        holder_email = holder.get("user_email") or ""
        return holder["user_id"] != user.id and holder_email.strip().lower() == user.email.strip().lower()

    @staticmethod
    async def _generate_key(client: httpx.AsyncClient, user: UserIdentity, api_key: str) -> None:
        """
        A concurrent first-login request may create the same deterministic key first. LiteLLM reports that as a
        duplicate alias (400) rather than a conflict, so a failure is accepted whenever the key exists afterwards.
        """
        # LiteLLM requires unique aliases across all keys, and display names are not unique.
        key_response = await client.post(
            "/key/generate",
            json={"key_alias": f"{user.name} ({user.id}) - Auto Generated Key", "user_id": user.id, "key": api_key},
        )
        if key_response.is_error and not await LiteLLMService._key_exists(client, api_key):
            key_response.raise_for_status()

    @staticmethod
    async def authorization_header_for_user(user: UserIdentity) -> dict[str, str]:
        """
        Pass this per request on the shared `LiteLLMProxySettings.httpx_aclient` rather than minting a client
        per user: httpx merges request headers over the client's, so the user's key wins over the master key.

        A per-user client would only differ by this header while owning a connection pool nothing bounds or
        evicts, growing with the user count for the process lifetime.
        """
        return {"Authorization": f"Bearer {await LiteLLMService.api_key_for_user(user)}"}

    @staticmethod
    async def openai_aclient_for_user(user: UserIdentity) -> openai.AsyncClient:
        """
        Scoped to the user's key, and callers must not close it — see `LiteLLMProxySettings.httpx_client`.

        `with_options` copies the shared client while reusing its underlying httpx client, so per-user
        authentication costs an object rather than a connection pool.
        """
        return LiteLLMProxySettings().openai_aclient.with_options(api_key=await LiteLLMService.api_key_for_user(user))
