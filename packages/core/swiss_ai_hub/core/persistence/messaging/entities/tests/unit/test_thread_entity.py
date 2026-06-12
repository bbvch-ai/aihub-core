import pytest

from swiss_ai_hub.core.persistence.messaging.entities.thread_entity import ThreadEntity


class TestGetOrderBy:
    """Pure unit tests for the sort-field → MongoEngine order_by string mapping."""

    @pytest.mark.parametrize(
        "sort_by, sort_order, expected",
        [
            ("created_at", -1, "-created_at"),
            ("created_at", 1, "created_at"),
            ("name", -1, "-name"),
            ("name", 1, "name"),
        ],
    )
    def test_valid_fields_map_to_prefixed_order(self, sort_by, sort_order, expected):
        assert ThreadEntity.get_order_by(sort_by, sort_order) == expected

    def test_unknown_field_falls_back_to_created_at_desc(self):
        assert ThreadEntity.get_order_by("llm_cost", 1) == "-created_at"
        assert ThreadEntity.get_order_by("", -1) == "-created_at"

    # Only -1 means descending, anything else is treated as ascending
    def test_non_negative_one_order_is_ascending(self):
        assert ThreadEntity.get_order_by("name", 1) == "name"
        assert ThreadEntity.get_order_by("name", 0) == "name"
