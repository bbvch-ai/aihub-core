from zoneinfo import ZoneInfo

import pytest

from swiss_ai_hub.core.scheduling.agent_schedule import AgentSchedule


class TestExpression:
    def test_joins_the_five_positions(self):
        schedule = AgentSchedule(minute="30", hour="9", day_of_month="1", month="*", day_of_week="*")
        assert schedule.expression == "30 9 1 * *"

    def test_defaults_to_hourly_on_the_hour(self):
        assert AgentSchedule().expression == "0 * * * *"

    def test_zone_info_resolves_the_timezone(self):
        assert AgentSchedule(timezone="Europe/Zurich").zone_info == ZoneInfo("Europe/Zurich")


class TestValidation:
    """Configuration-time rejection matters because the alternative is a scheduler that raises on
    every tick for a profile nobody can see is broken."""

    def test_rejects_out_of_range_position(self):
        with pytest.raises(ValueError, match="Invalid cron expression"):
            AgentSchedule(minute="99")

    def test_rejects_non_cron_text(self):
        with pytest.raises(ValueError, match="Invalid cron expression"):
            AgentSchedule(hour="noon")

    def test_rejects_unknown_timezone(self):
        with pytest.raises(ValueError, match="Unknown timezone"):
            AgentSchedule(timezone="Mars/Olympus")

    def test_accepts_step_and_list_syntax(self):
        assert AgentSchedule(minute="*/15", day_of_week="1,3,5").expression == "*/15 * * * 1,3,5"
