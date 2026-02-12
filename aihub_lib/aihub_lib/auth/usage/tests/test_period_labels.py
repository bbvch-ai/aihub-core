import pytest

from aihub_lib.auth.usage.AccessRuleDescriber import AccessRuleDescriber
from aihub_lib.auth.usage.usage_limit_models import RoleUsageLimitStatus, UsageLimitPeriod, UsageStatus
from aihub_lib.auth.usage.UsageLimitMessages import UsageLimitMessages

describe_pattern = AccessRuleDescriber.describe_pattern
get_period_label = AccessRuleDescriber.get_period_label
build_exceeded_detail = UsageLimitMessages.build_exceeded_detail


class TestPeriodLabels:
    """Tests for period labels loaded from i18n YAML files."""

    def test_all_periods_have_labels_in_all_locales(self):
        """All usage limit periods resolve to a non-empty label in every locale."""
        for period in UsageLimitPeriod:
            for locale in ("en", "de", "fr", "it"):
                label = get_period_label(period, locale)
                assert label and label != period.value, f"Missing {locale} label for period {period.value}"


class TestGetPeriodLabel:
    """Tests for get_period_label function."""

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
    """Tests for describe_pattern function."""

    def test_catch_all_greater_than(self):
        """Default locale is German (project convention)."""
        assert describe_pattern("aihub.user.agent.>") == "alle Agenten"

    def test_catch_all_star(self):
        """Default locale is German (project convention)."""
        assert describe_pattern("aihub.user.agent.*") == "alle Agenten"

    def test_double_wildcard(self):
        """Default locale is German (project convention)."""
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


class TestBuildExceededDetail:
    """Tests for build_exceeded_detail function."""

    def _make_status(self, *limit_tuples: tuple[str, int, UsageLimitPeriod, int, bool]) -> UsageStatus:
        """Helper: create UsageStatus from (pattern, limit, period, current_count, is_exceeded) tuples."""
        limits = [
            RoleUsageLimitStatus(
                pattern=pattern, limit=limit, period=period, current_count=count, reset_at=None, is_exceeded=exceeded
            )
            for pattern, limit, period, count, exceeded in limit_tuples
        ]
        return UsageStatus(limits=limits, is_exceeded=any(exceeded for *_, exceeded in limit_tuples))

    def test_includes_limits_array(self):
        """The detail contains a limits array with all limits and human-readable fields."""
        status = self._make_status(
            ("aihub.user.agent.>", 10, UsageLimitPeriod.ONE_HOUR, 10, True),
            ("aihub.user.agent.MyAgent.default", 100, UsageLimitPeriod.ONE_DAY, 50, False),
        )
        detail = build_exceeded_detail(status)

        assert detail.error == "usage_limit_exceeded"
        assert len(detail.limits) == 2
        assert detail.limits[0].is_exceeded is True
        assert detail.limits[0].scope["en"] == "all agents"
        assert detail.limits[0].period_label["en"] == "hour"
        assert detail.limits[1].is_exceeded is False
        assert detail.limits[1].scope["en"] == "MyAgent/default"
        assert detail.limits[1].period_label["de"] == "Tag"

    def test_aggregate_fields(self):
        """The detail includes aggregate single-limit fields."""
        status = self._make_status(("aihub.user.agent.>", 10, UsageLimitPeriod.ONE_HOUR, 10, True))
        detail = build_exceeded_detail(status)

        assert detail.limit == 10
        assert detail.period == UsageLimitPeriod.ONE_HOUR
        assert detail.current_count == 10

    def test_message_field_present_and_localized(self):
        """The detail includes a pre-formatted message string."""
        status = self._make_status(("aihub.user.agent.>", 10, UsageLimitPeriod.ONE_HOUR, 10, True))
        detail_en = build_exceeded_detail(status, locale="en")
        detail_de = build_exceeded_detail(status, locale="de")

        assert isinstance(detail_en.message, str)
        assert "10/10" in detail_en.message
        assert "hour" in detail_en.message

        assert isinstance(detail_de.message, str)
        assert "10/10" in detail_de.message
        assert "Stunde" in detail_de.message

    def test_reset_fields_none_when_no_reset(self):
        """Reset fields are None when no reset_at is available."""
        status = self._make_status(("aihub.user.agent.>", 10, UsageLimitPeriod.ONE_HOUR, 10, True))
        detail = build_exceeded_detail(status)

        assert detail.reset_at is None
        assert detail.reset_at_local is None
        assert detail.reset_in_seconds is None
