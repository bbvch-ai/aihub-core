from zoneinfo import ZoneInfo

import pytest
from pydantic import ValidationError

from swiss_ai_hub.core.scheduling.agent_schedule import AgentSchedule


class TestExpression:
    def test_joins_the_five_positions(self):
        schedule = AgentSchedule(minute="30", hour="9", day_of_month="1", month="*", day_of_week="*")
        assert schedule.expression == "30 9 1 * *"

    def test_timezone_defaults_to_utc(self):
        assert AgentSchedule(minute="0", hour="*", day_of_month="*", month="*", day_of_week="*").timezone == "UTC"

    def test_zone_info_resolves_the_timezone(self):
        schedule = AgentSchedule(
            minute="0", hour="*", day_of_month="*", month="*", day_of_week="*", timezone="Europe/Zurich"
        )
        assert schedule.zone_info == ZoneInfo("Europe/Zurich")


class TestValidation:
    """Configuration-time rejection matters because the alternative is a scheduler that raises on
    every tick for a profile nobody can see is broken."""

    def test_rejects_out_of_range_position(self):
        with pytest.raises(ValueError, match="Invalid cron expression"):
            AgentSchedule(minute="99", hour="*", day_of_month="*", month="*", day_of_week="*")

    def test_rejects_non_cron_text(self):
        with pytest.raises(ValueError, match="Invalid cron expression"):
            AgentSchedule(minute="0", hour="noon", day_of_month="*", month="*", day_of_week="*")

    def test_rejects_unknown_timezone(self):
        with pytest.raises(ValueError, match="Unknown timezone"):
            AgentSchedule(
                minute="0", hour="*", day_of_month="*", month="*", day_of_week="*", timezone="Mars/Olympus"
            )

    def test_accepts_step_and_list_syntax(self):
        schedule = AgentSchedule(minute="*/15", hour="*", day_of_month="*", month="*", day_of_week="1,3,5")
        assert schedule.expression == "*/15 * * * 1,3,5"

    def test_rejects_a_payload_that_omits_positions(self):
        """A dict that is not a schedule must fail loudly rather than default into an hourly cron —
        otherwise a stray value in config_data silently starts unattended runs nobody asked for."""
        with pytest.raises(ValidationError):
            AgentSchedule.model_validate({"$formkit": "cronInput", "label": "Schedule"})

    def test_rejects_unknown_keys(self):
        with pytest.raises(ValidationError):
            AgentSchedule.model_validate(
                {"minute": "0", "hour": "*", "day_of_month": "*", "month": "*", "day_of_week": "*", "label": "x"}
            )
