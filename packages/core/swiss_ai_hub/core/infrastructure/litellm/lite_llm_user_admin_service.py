from typing import Any, ClassVar

from swiss_ai_hub.core.infrastructure.litellm.lite_llm_proxy_settings import LiteLLMProxySettings
from swiss_ai_hub.core.infrastructure.litellm.lite_llm_user_limits import LiteLLMUserLimits


class LiteLLMUserAdminService:
    """
    Changes LiteLLM users after `LiteLLMService` created them: their limits, whether their keys work, and whether they
    exist at all. Every call uses the master key.
    """

    # The role `LiteLLMService` gives every user it creates. Nothing else in the platform creates users with it, so it
    # tells the Hub's users apart from LiteLLM's own admin and from users made by hand in the LiteLLM UI.
    HUB_USER_ROLE: ClassVar[str] = "internal_user_viewer"
    # Set on the user while the Hub holds their keys blocked, so that re-enabling the user unblocks only what the Hub
    # blocked: a key an operator blocked by hand stays blocked.
    KEYS_BLOCKED_BY_HUB: ClassVar[str] = "keys_blocked_by_swiss_ai_hub"
    # The largest page `/user/list` and `/key/list` serve.
    _PAGE_SIZE: ClassVar[int] = 100

    @staticmethod
    async def list_users() -> list[dict[str, Any]]:
        return await LiteLLMUserAdminService._all_pages(
            "/user/list", "users", {"page_size": LiteLLMUserAdminService._PAGE_SIZE}
        )

    @staticmethod
    async def list_keys() -> list[dict[str, Any]]:
        """Every live key, blocked ones included, as full objects: `/key/block` takes the hashed token they carry."""
        return await LiteLLMUserAdminService._all_pages(
            "/key/list", "keys", {"size": LiteLLMUserAdminService._PAGE_SIZE, "return_full_object": "true"}
        )

    @staticmethod
    async def update_limits(user_id: str, limits: LiteLLMUserLimits, current: LiteLLMUserLimits | None = None) -> bool:
        """
        Sends only the fields that differ from the user's row, read from LiteLLM unless the caller already has it.
        Returns whether anything was sent.

        LiteLLM drops its cached user on a budget or rate-limit change, and serves a new budget period once its
        60-second cache expires, so a change applies within a minute.
        """
        if current is None:
            current = await LiteLLMUserAdminService._limits_of(user_id)
        changes = limits.changes_from(current)
        if changes:
            await LiteLLMUserAdminService._update_user(user_id, changes)
        return bool(changes)

    @staticmethod
    def keys_blocked_by_hub(user_row: dict[str, Any]) -> bool:
        return bool((user_row.get("metadata") or {}).get(LiteLLMUserAdminService.KEYS_BLOCKED_BY_HUB))

    @staticmethod
    async def block_keys(user_row: dict[str, Any], keys: list[dict[str, Any]]) -> None:
        """
        LiteLLM cannot block a user (`blocked` on `/user/update` is not implemented in v1.106.4), so each of their keys
        is blocked instead. The Hub keeps handing out a blocked key rather than minting a new one, so the user stays
        locked out until their keys are unblocked.

        The user is marked first: a run that fails half-way leaves the mark, and either the next run blocks the rest
        or re-enabling the user unblocks what was blocked. Marking last could leave keys blocked that nothing unblocks.
        """
        if not LiteLLMUserAdminService.keys_blocked_by_hub(user_row):
            await LiteLLMUserAdminService._mark_keys_blocked(user_row, True)
        for key in keys:
            if not key.get("blocked"):
                await LiteLLMUserAdminService._post("/key/block", {"key": key["token"]})

    @staticmethod
    async def unblock_keys(user_row: dict[str, Any], keys: list[dict[str, Any]]) -> None:
        """The mark is cleared last, so a run that fails half-way is finished by the next one."""
        for key in keys:
            if key.get("blocked"):
                await LiteLLMUserAdminService._post("/key/unblock", {"key": key["token"]})
        await LiteLLMUserAdminService._mark_keys_blocked(user_row, False)

    @staticmethod
    async def delete_user(user_id: str) -> None:
        """
        Deletes the user together with their keys. Their spend stays in LiteLLM's spend logs and daily totals, which
        `/user/delete` leaves alone.
        """
        response = await LiteLLMProxySettings().httpx_aclient.post("/user/delete", json={"user_ids": [user_id]})
        # A run that outlived its lease may race the next one to the same user.
        if response.status_code != 404:
            response.raise_for_status()

    @staticmethod
    async def _mark_keys_blocked(user_row: dict[str, Any], blocked: bool) -> None:
        """
        LiteLLM replaces the whole metadata on update and ignores an empty one, so the mark is merged into what the
        user has and cleared by setting it false rather than by removing it.
        """
        metadata = {**(user_row.get("metadata") or {}), LiteLLMUserAdminService.KEYS_BLOCKED_BY_HUB: blocked}
        await LiteLLMUserAdminService._update_user(user_row["user_id"], {"metadata": metadata})

    @staticmethod
    async def _limits_of(user_id: str) -> LiteLLMUserLimits:
        response = await LiteLLMProxySettings().httpx_aclient.get("/user/info", params={"user_id": user_id})
        response.raise_for_status()
        return LiteLLMUserLimits.from_user_row(response.json()["user_info"])

    @staticmethod
    async def _update_user(user_id: str, fields: dict[str, Any]) -> None:
        await LiteLLMUserAdminService._post("/user/update", {"user_id": user_id, **fields})

    @staticmethod
    async def _post(path: str, body: dict[str, Any]) -> None:
        response = await LiteLLMProxySettings().httpx_aclient.post(path, json=body)
        response.raise_for_status()

    @staticmethod
    async def _all_pages(path: str, items_key: str, params: dict[str, Any]) -> list[dict[str, Any]]:
        client = LiteLLMProxySettings().httpx_aclient
        items: list[dict[str, Any]] = []
        page = 1
        while True:
            response = await client.get(path, params={**params, "page": page})
            response.raise_for_status()
            body = response.json()
            items.extend(body[items_key])
            if page >= (body.get("total_pages") or 1):
                return items
            page += 1
