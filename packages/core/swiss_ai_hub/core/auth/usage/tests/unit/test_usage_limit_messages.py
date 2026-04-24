from swiss_ai_hub.core.auth.usage.usage_limit_messages import UsageLimitMessages
from swiss_ai_hub.core.auth.usage.usage_limit_models import RoleUsageLimitStatus, UsageLimitPeriod, UsageStatus
from swiss_ai_hub.core.testing.auth_utils.user_mocks import mock_keycloak_admin_service_autouse  # noqa: F401

build_exceeded_detail = UsageLimitMessages.build_exceeded_detail


class TestBuildExceededDetail:
    """Tests for UsageLimitMessages.build_exceeded_detail."""

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
