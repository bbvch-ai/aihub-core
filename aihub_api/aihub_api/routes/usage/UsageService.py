from datetime import datetime

from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.infrastructure.litellm.LiteLLMProxySettings import LiteLLMProxySettings
from fastapi import HTTPException

from aihub_api.routes.usage.dto.UserUsageDTO import UserUsageDTO


class UsageService:
    """Service for retrieving user usage and budget information from LiteLLM."""

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
        )

    @staticmethod
    async def check_user_budget(user: UserIdentity) -> None:
        """
        Check if user has exceeded their budget and raise HTTPException if so.

        This should be called before executing expensive operations like agent runs.
        Raises HTTP 429 (Too Many Requests) with budget details if limit exceeded.
        """
        try:
            usage = await UsageService.get_user_usage(user)
        except Exception:
            # If we can't check the budget, allow the request to proceed
            # This prevents blocking users if LiteLLM is temporarily unavailable
            return

        if usage.is_over_limit:
            reset_info = ""
            if usage.budget_reset_at:
                reset_info = f" Budget resets at {usage.budget_reset_at.isoformat()}."

            raise HTTPException(
                status_code=429,
                detail=f"Budget limit exceeded. You have spent ${usage.spend:.2f} of your "
                f"${usage.max_budget:.2f} budget.{reset_info}",
            )
