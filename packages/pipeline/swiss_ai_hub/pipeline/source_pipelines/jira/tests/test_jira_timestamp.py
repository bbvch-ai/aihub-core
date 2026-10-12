from datetime import UTC, datetime
from zoneinfo import ZoneInfo

import pytest

from swiss_ai_hub.pipeline.source_pipelines.jira.jira_timestamp import JiraTimestamp

_ZURICH = ZoneInfo("Europe/Zurich")


class TestJqlLowerBound:
    def test_no_cursor_means_no_bound(self):
        assert JiraTimestamp.jql_lower_bound(None, _ZURICH) is None

    def test_the_cursor_is_written_in_the_account_s_zone_floored_to_the_minute(self):
        """Jira reads JQL dates in the API user's zone, to the minute; flooring never starts after the cursor."""
        start = datetime(2026, 10, 8, 8, 5, 59, 999000, tzinfo=UTC)

        assert JiraTimestamp.jql_lower_bound(start, _ZURICH) == "2026/10/08 10:05"

    @pytest.mark.parametrize("utc_hour", [0, 1])
    def test_a_time_the_clocks_pass_twice_is_moved_an_hour_back(self, utc_hour: int):
        """On 2026-10-25 Zurich passes 02:30 twice (00:30 and 01:30 UTC); Jira may read it as the later one."""
        start = datetime(2026, 10, 25, utc_hour, 30, tzinfo=UTC)

        assert JiraTimestamp.jql_lower_bound(start, _ZURICH) == "2026/10/25 01:30"

    def test_the_start_of_summer_time_needs_no_correction(self):
        start = datetime(2026, 3, 29, 1, 30, tzinfo=UTC)

        assert JiraTimestamp.jql_lower_bound(start, _ZURICH) == "2026/03/29 03:30"

    def test_a_naive_cursor_is_read_as_utc(self):
        assert JiraTimestamp.jql_lower_bound(datetime(2026, 10, 8, 8, 5), _ZURICH) == "2026/10/08 10:05"


class TestZone:
    def test_the_account_s_zone_is_used_and_utc_without_one(self):
        assert JiraTimestamp.zone_of({"timeZone": "Asia/Ho_Chi_Minh"}) == ZoneInfo("Asia/Ho_Chi_Minh")
        assert JiraTimestamp.zone_of({}) == ZoneInfo("UTC")

    def test_a_jira_timestamp_becomes_aware_utc(self):
        assert JiraTimestamp.to_utc("2026-10-08T10:15:30.000+0200") == datetime(2026, 10, 8, 8, 15, 30, tzinfo=UTC)
