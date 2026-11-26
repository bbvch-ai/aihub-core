import hashlib

import pytest
from bson import ObjectId
from cryptography.fernet import Fernet

from swiss_ai_hub.core.persistence.messaging.entities.thread_entity import AgentInstanceRef, ThreadEntity

ENCRYPTION_KEY_VARIABLE = "AIHUB_CONFIG_ENCRYPTION_KEY"


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
    thread, without a lookup two replicas could race into creating a second one. The instance key in the
    derivation is what keeps a client from computing the id and creating the thread before the first run."""

    PROFILE = AgentInstanceRef(agent_class="ImapAgent", agent_id="inbox-1")

    @pytest.fixture(autouse=True)
    def _instance_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(ENCRYPTION_KEY_VARIABLE, Fernet.generate_key().decode())

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

    def test_is_not_the_digest_of_the_profile_alone(self):
        """The unkeyed digest is what scheduled threads used before, and what anyone can compute."""
        unkeyed = ObjectId(hashlib.sha256(b"ImapAgent/inbox-1").digest()[:12])

        assert ThreadEntity.scheduled_thread_id(self.PROFILE) != unkeyed

    def test_differs_per_instance_key(self, monkeypatch: pytest.MonkeyPatch):
        first = ThreadEntity.scheduled_thread_id(self.PROFILE)
        monkeypatch.setenv(ENCRYPTION_KEY_VARIABLE, Fernet.generate_key().decode())

        assert ThreadEntity.scheduled_thread_id(self.PROFILE) != first

    @pytest.mark.parametrize("key", ["", "REPLACE_WITH_FERNET_KEY"])
    def test_refuses_an_instance_without_a_real_key(self, monkeypatch: pytest.MonkeyPatch, key: str):
        """The `.env.prod` placeholder is public, so an id keyed with it could be computed again."""
        monkeypatch.setenv(ENCRYPTION_KEY_VARIABLE, key)

        with pytest.raises(ValueError):
            ThreadEntity.scheduled_thread_id(self.PROFILE)
