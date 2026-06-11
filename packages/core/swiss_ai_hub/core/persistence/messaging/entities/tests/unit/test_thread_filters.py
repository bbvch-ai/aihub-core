from datetime import datetime

from swiss_ai_hub.core.persistence.messaging.entities.types.thread_filters import ThreadFilters


class TestThreadFilters:
    def test_defaults_are_all_none(self):
        f = ThreadFilters()
        assert f.search is None
        assert f.agent_id is None
        assert f.user_search_id is None
        assert f.status_thread_ids is None
        assert f.from_date is None
        assert f.to_date is None

    def test_date_only_iso_string_parses_to_midnight(self):
        f = ThreadFilters(from_date="2026-06-09", to_date="2026-06-10")
        assert f.from_date == datetime(2026, 6, 9, 0, 0, 0)
        assert f.to_date == datetime(2026, 6, 10, 0, 0, 0)

    def test_full_iso_string_parses_with_time(self):
        f = ThreadFilters(from_date="2026-06-09T13:30:00")
        assert f.from_date == datetime(2026, 6, 9, 13, 30, 0)

    def test_datetime_passthrough(self):
        dt = datetime(2026, 1, 1, 8, 0, 0)
        assert ThreadFilters(from_date=dt).from_date == dt

    def test_status_thread_ids_list_is_preserved(self):
        f = ThreadFilters(status_thread_ids=["a", "b"])
        assert f.status_thread_ids == ["a", "b"]
