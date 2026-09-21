import pytest

from swiss_ai_hub.core.persistence.messaging.entities.thread_entity import AgentInstanceRef, ThreadEntity


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


class TestScheduledThreadId:
    """Deriving the id from the profile is what lets every scheduled run of that profile land in one
    thread, without a lookup two replicas could race into creating a second one."""

    def test_is_stable_for_the_same_profile(self):
        """Two equal refs, not one ref twice: the id has to survive the process that built it, since
        the replica resolving the thread is rarely the one that created it."""
        first = AgentInstanceRef(agent_class="ImapAgent", agent_id="inbox-1")
        second = AgentInstanceRef(agent_class="ImapAgent", agent_id="inbox-1")

        assert ThreadEntity.scheduled_thread_id(first) == ThreadEntity.scheduled_thread_id(second)

    def test_differs_per_profile_of_one_class(self):
        first = AgentInstanceRef(agent_class="ImapAgent", agent_id="inbox-1")
        second = AgentInstanceRef(agent_class="ImapAgent", agent_id="inbox-2")

        assert ThreadEntity.scheduled_thread_id(first) != ThreadEntity.scheduled_thread_id(second)

    def test_differs_per_class_for_one_profile_slug(self):
        first = AgentInstanceRef(agent_class="ImapAgent", agent_id="daily")
        second = AgentInstanceRef(agent_class="ReportAgent", agent_id="daily")

        assert ThreadEntity.scheduled_thread_id(first) != ThreadEntity.scheduled_thread_id(second)
