from datetime import datetime, timezone

import pytest

from aihub_lib.auth.usage.period_labels import (
    PERIOD_LABELS,
    build_exceeded_detail,
    build_usage_limit_messages,
    describe_pattern,
    get_period_label,
)
from aihub_lib.auth.usage.UsageLimitService import EffectiveLimitStatus, UsageLimitPeriod, UsageStatus


class TestPeriodLabels:
    """Tests for period label constants."""

    def test_all_periods_have_labels(self):
        """All usage limit periods have corresponding labels."""
        for period in UsageLimitPeriod:
            assert period.value in PERIOD_LABELS, f"Missing label for period {period.value}"

    def test_all_labels_have_all_languages(self):
        """Each period label has translations for all supported languages."""
        for period, label in PERIOD_LABELS.items():
            assert label.en is not None, f"Missing English label for {period}"
            assert label.de is not None, f"Missing German label for {period}"
            assert label.fr is not None, f"Missing French label for {period}"
            assert label.it is not None, f"Missing Italian label for {period}"


class TestGetPeriodLabel:
    """Tests for get_period_label function."""

    def test_returns_english_label_by_default(self):
        """Default locale is English."""
        assert get_period_label("1d") == "day"

    def test_returns_german_label(self):
        """Returns German label when requested."""
        assert get_period_label("1d", "de") == "Tag"

    def test_returns_french_label(self):
        """Returns French label when requested."""
        assert get_period_label("1d", "fr") == "jour"

    def test_returns_italian_label(self):
        """Returns Italian label when requested."""
        assert get_period_label("1d", "it") == "giorno"

    def test_returns_period_for_unknown_period(self):
        """Returns the period string itself for unknown periods."""
        assert get_period_label("unknown_period") == "unknown_period"

    def test_returns_empty_for_none_period(self):
        """Returns empty string for None period."""
        assert get_period_label(None) == ""

    @pytest.mark.parametrize(
        "period,expected_en",
        [
            ("1h", "hour"),
            ("1d", "day"),
            ("7d", "week"),
            ("1mo", "month"),
        ],
    )
    def test_all_period_labels_english(self, period: str, expected_en: str):
        """Verify all English period labels are correct."""
        assert get_period_label(period, "en") == expected_en


class TestBuildUsageLimitMessages:
    """Tests for build_usage_limit_messages function."""

    def test_returns_all_languages(self):
        """Messages are built for all supported languages."""
        messages = build_usage_limit_messages(100, "1d")

        assert messages.en is not None
        assert messages.de is not None
        assert messages.fr is not None
        assert messages.it is not None

    def test_english_message_format(self):
        """English message has correct format."""
        messages = build_usage_limit_messages(100, "1d")

        assert messages.en == "Usage limit reached: 100 agent calls per day"

    def test_german_message_format(self):
        """German message has correct format."""
        messages = build_usage_limit_messages(100, "1d")

        assert messages.de == "Nutzungslimit erreicht: 100 Agentenaufrufe pro Tag"

    def test_french_message_format(self):
        """French message has correct format."""
        messages = build_usage_limit_messages(100, "1d")

        assert messages.fr == "Limite d'utilisation atteinte: 100 appels d'agent par jour"

    def test_italian_message_format(self):
        """Italian message has correct format."""
        messages = build_usage_limit_messages(100, "1d")

        assert messages.it == "Limite di utilizzo raggiunto: 100 chiamate agente per giorno"

    def test_fallback_when_limit_is_none(self):
        """Returns generic message when limit is None."""
        messages = build_usage_limit_messages(None, "1d")

        assert messages.en == "Usage limit exceeded"
        assert messages.de == "Nutzungslimit erreicht"

    def test_fallback_when_period_is_none(self):
        """Returns generic message when period is None."""
        messages = build_usage_limit_messages(100, None)

        assert messages.en == "Usage limit exceeded"
        assert messages.de == "Nutzungslimit erreicht"

    @pytest.mark.parametrize(
        "period,expected_period_en",
        [
            ("1h", "hour"),
            ("1d", "day"),
            ("7d", "week"),
            ("1mo", "month"),
        ],
    )
    def test_all_periods_in_messages(self, period: str, expected_period_en: str):
        """All periods are correctly translated in messages."""
        messages = build_usage_limit_messages(50, period)

        assert expected_period_en in messages.en


class TestDescribePattern:
    """Tests for describe_pattern function."""

    def test_catch_all_greater_than(self):
        assert describe_pattern("aihub.user.agent.>") == "all agents"

    def test_catch_all_star(self):
        assert describe_pattern("aihub.user.agent.*") == "all agents"

    def test_double_wildcard(self):
        assert describe_pattern("aihub.user.agent.*.*") == "all agents"

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

    def _make_status(self, *limit_tuples: tuple[str, int, str, int, bool]) -> UsageStatus:
        """Helper: create UsageStatus from (pattern, limit, period, current_count, is_exceeded) tuples."""
        limits = [
            EffectiveLimitStatus(
                pattern=p, limit=l, period=per, current_count=c, reset_at=None, is_exceeded=e
            )
            for p, l, per, c, e in limit_tuples
        ]
        return UsageStatus(limits=limits, is_exceeded=any(e for *_, e in limit_tuples))

    def test_includes_limits_array(self):
        """The detail dict contains a 'limits' array with all limits and human-readable fields."""
        status = self._make_status(
            ("aihub.user.agent.>", 10, "1h", 10, True),
            ("aihub.user.agent.MyAgent.default", 100, "1d", 50, False),
        )
        detail = build_exceeded_detail(status)

        assert detail["error"] == "usage_limit_exceeded"
        assert len(detail["limits"]) == 2
        assert detail["limits"][0]["is_exceeded"] is True
        assert detail["limits"][0]["scope"]["en"] == "all agents"
        assert detail["limits"][0]["period_label"]["en"] == "hour"
        assert detail["limits"][1]["is_exceeded"] is False
        assert detail["limits"][1]["scope"]["en"] == "MyAgent/default"
        assert detail["limits"][1]["period_label"]["de"] == "Tag"

    def test_backward_compat_fields(self):
        """The detail dict includes backward-compatible single-limit fields."""
        status = self._make_status(("aihub.user.agent.>", 10, "1h", 10, True))
        detail = build_exceeded_detail(status)

        assert detail["limit"] == 10
        assert detail["period"] == "1h"
        assert detail["current_count"] == 10

    def test_messages_present(self):
        """The detail dict includes translated messages."""
        status = self._make_status(("aihub.user.agent.>", 10, "1h", 10, True))
        detail = build_exceeded_detail(status)

        assert "en" in detail["messages"]
        assert "de" in detail["messages"]

    def test_reset_fields_none_when_no_reset(self):
        """Reset fields are None when no reset_at is available."""
        status = self._make_status(("aihub.user.agent.>", 10, "1h", 10, True))
        detail = build_exceeded_detail(status)

        assert detail["reset_at"] is None
        assert detail["reset_at_local"] is None
        assert detail["reset_in_seconds"] is None
