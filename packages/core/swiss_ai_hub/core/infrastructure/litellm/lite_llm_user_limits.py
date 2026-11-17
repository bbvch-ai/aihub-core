from typing import Annotated, Any, Self

from pydantic import BaseModel, Field

from swiss_ai_hub.core.infrastructure.litellm.lite_llm_proxy_settings import LiteLLMProxySettings


class LiteLLMUserLimits(BaseModel):
    """
    The limits the Hub keeps in step on a user's LiteLLM row.

    Only fields LiteLLM v1.106.4 can both set and clear on an existing user belong here. It drops a null
    `max_parallel_requests` from `/user/update` and has no `soft_budget` there at all, so those two are set when the
    user is created and never changed.
    """

    max_budget: Annotated[float | None, Field(description="Spend allowed per budget period.")] = None
    budget_duration: Annotated[str | None, Field(description='Budget period, such as "30d"; none never resets.')] = None
    tpm_limit: Annotated[int | None, Field(description="Tokens per minute.")] = None
    rpm_limit: Annotated[int | None, Field(description="Requests per minute.")] = None

    @classmethod
    def from_settings(cls, settings: LiteLLMProxySettings) -> Self:
        return cls(
            max_budget=settings.USER_MAX_BUDGET,
            budget_duration=settings.USER_BUDGET_DURATION,
            tpm_limit=settings.USER_TPM_LIMIT,
            rpm_limit=settings.USER_RPM_LIMIT,
        )

    @classmethod
    def from_user_row(cls, user_row: dict[str, Any]) -> Self:
        return cls(**{field: user_row.get(field) for field in cls.model_fields})

    def changes_from(self, current: Self) -> dict[str, Any]:
        """
        Only the fields that differ, because resending `budget_duration` starts the user's budget period anew: a
        reconciliation that sent every field on every run would keep the budget from ever resetting.
        """
        return {field: value for field, value in self.model_dump().items() if getattr(current, field) != value}
