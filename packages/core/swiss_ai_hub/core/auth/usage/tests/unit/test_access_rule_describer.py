import pytest

from swiss_ai_hub.core.auth.usage.access_rule_describer import AccessRuleDescriber
from swiss_ai_hub.core.auth.usage.usage_limit_models import UsageLimitPeriod

describe_pattern = AccessRuleDescriber.describe_pattern
get_period_label = AccessRuleDescriber.get_period_label


class TestPeriodLabels:
    """Tests for period labels loaded from i18n YAML files."""

    def test_all_periods_have_labels_in_all_locales(self):
        """All usage limit periods resolve to a non-empty label in every locale."""
        for period in UsageLimitPeriod:
            for locale in ("en", "de", "fr", "it"):
                label = get_period_label(period, locale)
                assert label and label != period.value, f"Missing {locale} label for period {period.value}"


class TestGetPeriodLabel:
    """Tests for AccessRuleDescriber.get_period_label."""

    def test_returns_german_label_by_default(self):
        """Default locale is German (project convention)."""
        assert get_period_label(UsageLimitPeriod.ONE_DAY) == "Tag"

    def test_returns_german_label(self):
        """Returns German label when requested."""
        assert get_period_label(UsageLimitPeriod.ONE_DAY, "de") == "Tag"

    def test_returns_french_label(self):
        """Returns French label when requested."""
        assert get_period_label(UsageLimitPeriod.ONE_DAY, "fr") == "jour"

    def test_returns_italian_label(self):
        """Returns Italian label when requested."""
        assert get_period_label(UsageLimitPeriod.ONE_DAY, "it") == "giorno"

    def test_returns_empty_for_none_period(self):
        """Returns empty string for None period."""
        assert get_period_label(None) == ""

    @pytest.mark.parametrize(
        "period,expected_en",
        [
            (UsageLimitPeriod.ONE_HOUR, "hour"),
            (UsageLimitPeriod.ONE_DAY, "day"),
            (UsageLimitPeriod.SEVEN_DAYS, "week"),
            (UsageLimitPeriod.ONE_MONTH, "month"),
        ],
    )
    def test_all_period_labels_english(self, period: UsageLimitPeriod, expected_en: str):
        """Verify all English period labels are correct."""
        assert get_period_label(period, "en") == expected_en


class TestDescribePattern:
    """Tests for AccessRuleDescriber.describe_pattern."""

    def test_catch_all_greater_than(self):
        assert describe_pattern("aihub.user.agent.>") == "alle Agenten"

    def test_catch_all_star(self):
        assert describe_pattern("aihub.user.agent.*") == "alle Agenten"

    def test_double_wildcard(self):
        assert describe_pattern("aihub.user.agent.*.*") == "alle Agenten"

    def test_class_wildcard(self):
        """Specific class with wildcard ID returns just the class name."""
        assert describe_pattern("aihub.user.agent.MyAgent.*") == "MyAgent"

    def test_fully_specific(self):
        """Fully specific pattern returns class/id."""
        assert describe_pattern("aihub.user.agent.MyAgent.v1") == "MyAgent/v1"

    def test_german_locale(self):
        assert describe_pattern("aihub.user.agent.>", "de") == "alle Agenten"

    def test_french_locale(self):
        assert describe_pattern("aihub.user.agent.>", "fr") == "tous les agents"
