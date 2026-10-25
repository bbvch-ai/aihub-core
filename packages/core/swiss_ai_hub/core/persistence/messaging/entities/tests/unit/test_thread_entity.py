from unittest.mock import MagicMock, patch

import pytest

from swiss_ai_hub.core.persistence.messaging.entities.thread_entity import AgentInstanceRef, ThreadEntity, User


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


class TestScheduledThreadReclaim:
    """The scheduled-run thread id is derivable from the profile, so a client may have created a chat thread
    under it first. Runs must never fire into such a thread."""

    AGENT = AgentInstanceRef(agent_class="ImapAgent", agent_id="inbox-1")
    MODULE = "swiss_ai_hub.core.persistence.messaging.entities.thread_entity"

    def _existing(self, **fields) -> ThreadEntity:
        defaults = {"name": "Scheduled runs", "users": [], "agents": [self.AGENT]}
        return ThreadEntity(id=ThreadEntity.scheduled_thread_id(self.AGENT), **(defaults | fields))

    def _resolve(self, existing: ThreadEntity) -> tuple[ThreadEntity | dict, MagicMock, MagicMock]:
        objects = MagicMock()
        objects.return_value.first.return_value = existing
        with (
            patch.object(ThreadEntity, "objects", objects),
            patch.object(ThreadEntity, "delete") as delete,
            patch.object(ThreadEntity, "create_thread", side_effect=lambda *args, **kwargs: kwargs),
            patch(f"{self.MODULE}.PersistedAgentEventEntity.delete_events_for_thread") as delete_events,
        ):
            thread = ThreadEntity.get_or_create_scheduled_thread("Scheduled runs", self.AGENT)
        return thread, delete, delete_events

    def test_keeps_the_genuine_scheduled_thread(self):
        existing = self._existing()

        thread, delete, delete_events = self._resolve(existing)

        assert thread is existing
        delete.assert_not_called()
        delete_events.assert_not_called()

    @pytest.mark.parametrize(
        "fields",
        [
            {"users": [User(user_id="someone")]},
            {"agents": [AgentInstanceRef(agent_class="RAGAgent", agent_id="other")]},
            {"process_class": "SomeProcess"},
        ],
    )
    def test_discards_a_thread_a_client_created_under_the_id(self, fields):
        thread, delete, delete_events = self._resolve(self._existing(**fields))

        delete.assert_called_once()
        delete_events.assert_called_once_with(str(ThreadEntity.scheduled_thread_id(self.AGENT)))
        assert thread["users"] == []
        assert thread["thread_id"] == ThreadEntity.scheduled_thread_id(self.AGENT)
