from datetime import datetime
from functools import lru_cache
from typing import Literal

from aihub_lib.auth.access.RoleLimitService import RoleLimitService
from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.infrastructure.litellm.LiteLLMProxySettings import LiteLLMProxySettings
from aihub_lib.infrastructure.redis.RedisSettings import RedisSettings
from fastapi import HTTPException
from redis.asyncio import Redis

from aihub_api.routes.usage.dto.UserUsageDTO import AgentUsageDTO, UserUsageDTO


@lru_cache
def _get_redis_client() -> Redis:
    """Cached Redis client instance."""
    return RedisSettings.create_client()


# User-friendly budget exceeded messages in multiple languages
BUDGET_EXCEEDED_MESSAGES = {
    "en": {
        "title": "Usage Limit Reached",
        "message": "You've reached your usage limit for this period.",
        "details": "Current usage: {usage_percent:.0f}%",
        "reset": "Your limit will reset on {reset_date}.",
        "contact": "Please contact your administrator if you need additional capacity.",
    },
    "de": {
        "title": "Nutzungslimit erreicht",
        "message": "Sie haben Ihr Nutzungslimit für diesen Zeitraum erreicht.",
        "details": "Aktuelle Nutzung: {usage_percent:.0f}%",
        "reset": "Ihr Limit wird am {reset_date} zurückgesetzt.",
        "contact": "Bitte kontaktieren Sie Ihren Administrator, wenn Sie zusätzliche Kapazität benötigen.",
    },
    "fr": {
        "title": "Limite d'utilisation atteinte",
        "message": "Vous avez atteint votre limite d'utilisation pour cette période.",
        "details": "Utilisation actuelle: {usage_percent:.0f}%",
        "reset": "Votre limite sera réinitialisée le {reset_date}.",
        "contact": "Veuillez contacter votre administrateur si vous avez besoin de capacité supplémentaire.",
    },
    "it": {
        "title": "Limite di utilizzo raggiunto",
        "message": "Hai raggiunto il limite di utilizzo per questo periodo.",
        "details": "Utilizzo attuale: {usage_percent:.0f}%",
        "reset": "Il limite verrà ripristinato il {reset_date}.",
        "contact": "Contatta il tuo amministratore se hai bisogno di capacità aggiuntiva.",
    },
}


class UsageService:
    """Service for retrieving user usage and budget information from LiteLLM."""

    @staticmethod
    def _format_date(dt: datetime, locale: str) -> str:
        """Format date according to locale (DD.MM.YYYY for European, MM/DD/YYYY for English)."""
        if locale in ("de", "fr", "it"):
            return dt.strftime("%d.%m.%Y")
        return dt.strftime("%m/%d/%Y")

    @staticmethod
    def _get_budget_exceeded_message(
        usage: "UserUsageDTO",
        locale: Literal["en", "de", "fr", "it"] = "en",
    ) -> str:
        """Generate a user-friendly budget exceeded message."""
        messages = BUDGET_EXCEEDED_MESSAGES.get(locale, BUDGET_EXCEEDED_MESSAGES["en"])

        parts = [
            messages["title"],
            "",
            messages["message"],
            messages["details"].format(usage_percent=usage.usage_percent or 100),
        ]

        if usage.budget_reset_at:
            reset_date = UsageService._format_date(usage.budget_reset_at, locale)
            parts.append(messages["reset"].format(reset_date=reset_date))

        parts.append("")
        parts.append(messages["contact"])

        return "\n".join(parts)

    @staticmethod
    async def get_user_usage(user: UserIdentity) -> UserUsageDTO:
        """
        Retrieve current usage and budget information for a user from LiteLLM.

        Queries the LiteLLM proxy's /user/info endpoint to get spend data,
        budget limits, and rate limits for the specified user.
        """
        litellm_settings = LiteLLMProxySettings()
        client = litellm_settings.httpx_aclient

        response = await client.get("/user/info", params={"user_id": user.id})
        response.raise_for_status()

        data = response.json()
        user_info = data.get("user_info", {})

        spend = float(user_info.get("spend", 0) or 0)
        max_budget = user_info.get("max_budget")
        soft_budget = user_info.get("soft_budget")
        budget_duration = user_info.get("budget_duration")
        tpm_limit = user_info.get("tpm_limit")
        rpm_limit = user_info.get("rpm_limit")

        # Parse budget_reset_at if present
        budget_reset_at = None
        if user_info.get("budget_reset_at"):
            budget_reset_at = datetime.fromisoformat(user_info["budget_reset_at"].replace("Z", "+00:00"))

        # Calculate usage percentage
        usage_percent = None
        if max_budget and max_budget > 0:
            usage_percent = min((spend / max_budget) * 100, 100.0)

        # Determine warning states
        is_approaching_limit = False
        is_over_limit = False
        if max_budget and max_budget > 0:
            is_approaching_limit = spend >= (max_budget * 0.8)
            is_over_limit = spend >= max_budget

        # Get agent usage from role-based limits
        agent_usage_dto = None
        try:
            role_limit_service = RoleLimitService(redis=_get_redis_client())
            agent_usage = await role_limit_service.get_agent_usage(user)
            agent_usage_dto = AgentUsageDTO(
                current_count=agent_usage.current_count,
                limit=agent_usage.limit,
                period=agent_usage.period,
                reset_at=agent_usage.reset_at,
                usage_percent=agent_usage.usage_percent,
                is_over_limit=agent_usage.is_over_limit,
            )
        except Exception:
            # If we can't get agent usage, continue without it
            pass

        return UserUsageDTO(
            user_id=user.id,
            spend=spend,
            max_budget=max_budget,
            soft_budget=soft_budget,
            budget_duration=budget_duration,
            budget_reset_at=budget_reset_at,
            tpm_limit=tpm_limit,
            rpm_limit=rpm_limit,
            usage_percent=usage_percent,
            is_approaching_limit=is_approaching_limit,
            is_over_limit=is_over_limit,
            agent_usage=agent_usage_dto,
        )

    @staticmethod
    async def check_user_budget(
        user: UserIdentity,
        locale: Literal["en", "de", "fr", "it"] = "en",
    ) -> None:
        """
        Check if user has exceeded their budget and raise HTTPException if so.

        This should be called before executing expensive operations like agent runs.
        Raises HTTP 429 (Too Many Requests) with a user-friendly message if limit exceeded.
        """
        try:
            usage = await UsageService.get_user_usage(user)
        except Exception:
            # If we can't check the budget, allow the request to proceed
            # This prevents blocking users if LiteLLM is temporarily unavailable
            return

        if usage.is_over_limit:
            message = UsageService._get_budget_exceeded_message(usage, locale)
            raise HTTPException(status_code=429, detail=message)

    @staticmethod
    async def add_spend_to_user(user_id: str, amount: float) -> None:
        """
        Add spend amount to a user's current spend in LiteLLM.

        This can be used to attribute agent costs to individual users,
        since agents use a shared service account key.
        """
        if amount <= 0:
            return

        litellm_settings = LiteLLMProxySettings()
        client = litellm_settings.httpx_aclient

        # First get current spend
        response = await client.get("/user/info", params={"user_id": user_id})
        response.raise_for_status()
        current_spend = float(response.json().get("user_info", {}).get("spend", 0) or 0)

        # Update with new spend
        new_spend = current_spend + amount
        await client.post(
            "/user/update",
            json={"user_id": user_id, "spend": new_spend},
        )
