import pytest

from swiss_ai_hub.core.infrastructure.litellm.lite_llm_proxy_settings import LiteLLMProxySettings
from swiss_ai_hub.core.infrastructure.litellm.lite_llm_user_limits import LiteLLMUserLimits

pytestmark = pytest.mark.unit


def test_limits_come_from_the_user_settings() -> None:
    settings = LiteLLMProxySettings(
        BASE_URL="http://litellm:4000",
        USER_MAX_BUDGET=100.0,
        USER_BUDGET_DURATION="30d",
        USER_TPM_LIMIT=10_000,
        USER_RPM_LIMIT=60,
    )

    assert LiteLLMUserLimits.from_settings(settings) == LiteLLMUserLimits(
        max_budget=100.0, budget_duration="30d", tpm_limit=10_000, rpm_limit=60
    )


def test_a_user_row_is_read_without_its_other_fields() -> None:
    row = {"user_id": "u", "max_budget": 100, "budget_duration": "30d", "tpm_limit": None, "rpm_limit": 60, "spend": 3}

    assert LiteLLMUserLimits.from_user_row(row) == LiteLLMUserLimits(
        max_budget=100.0, budget_duration="30d", rpm_limit=60
    )


def test_unchanged_limits_produce_no_changes() -> None:
    limits = LiteLLMUserLimits(max_budget=100.0, budget_duration="30d", tpm_limit=10_000, rpm_limit=60)

    assert limits.changes_from(limits.model_copy()) == {}


def test_only_the_changed_fields_are_returned() -> None:
    """The unchanged budget period must not be resent, or LiteLLM would restart it."""
    current = LiteLLMUserLimits(max_budget=100.0, budget_duration="30d", rpm_limit=60)
    desired = LiteLLMUserLimits(max_budget=50.0, budget_duration="30d", rpm_limit=60)

    assert desired.changes_from(current) == {"max_budget": 50.0}


def test_a_removed_limit_is_sent_as_null() -> None:
    current = LiteLLMUserLimits(tpm_limit=10_000)

    assert LiteLLMUserLimits().changes_from(current) == {"tpm_limit": None}
