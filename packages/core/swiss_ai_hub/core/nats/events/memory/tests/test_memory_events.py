import pytest

from swiss_ai_hub.core.infrastructure.mem0.types.Memory import Memory
from swiss_ai_hub.core.infrastructure.mem0.types.MemoryAdded import MemoryAdded
from swiss_ai_hub.core.infrastructure.mem0.types.MemoryEventType import MemoryEventType
from swiss_ai_hub.core.infrastructure.mem0.types.MemoryMetadata import MemoryMetadata
from swiss_ai_hub.core.infrastructure.mem0.types.MemoryRelation import MemoryRelation
from swiss_ai_hub.core.infrastructure.mem0.types.MemorySearchResult import MemorySearchResult
from swiss_ai_hub.core.infrastructure.mem0.types.MemoryType import MemoryType
from swiss_ai_hub.core.infrastructure.mem0.types.ModifiedMemory import ModifiedMemory
from swiss_ai_hub.core.infrastructure.mem0.types.ModifiedRelations import ModifiedRelations
from swiss_ai_hub.core.nats.events.memory.retrieve.BaseRetrieveMemoryEvent import BaseRetrieveMemoryEvent
from swiss_ai_hub.core.nats.events.memory.store.StoreUserMemoryEvent import StoreUserMemoryEvent


class TestStoreUserMemoryEvent:
    """Tests for StoreUserMemoryEvent factory method."""

    @pytest.fixture
    def sample_metadata(self):
        """Sample memory metadata for tests."""
        return MemoryMetadata(
            user_id="test_user",
            agent_id="TestAgent/test_1",
            thread_id="thread_123",
            display_id="display_456",
            run_id="run_789",
            type=MemoryType.USER_MEMORY,
        )

    def test_from_memory_added_object_with_additions(self, sample_metadata):
        """Should extract added memories from MemoryAdded object."""
        memory_added = MemoryAdded(
            owner_id="test_user",
            _user_id="test_user",
            _agent_id="TestAgent/test_1",
            _thread_id="thread_123",
            _display_id="display_456",
            _run_id="run_789",
            _type=MemoryType.USER_MEMORY,
            _tenant_id=None,
            _tenant_namespace=None,
            results=[
                ModifiedMemory(id="mem_1", memory="User likes Python", event=MemoryEventType.ADD),
                ModifiedMemory(id="mem_2", memory="User works at ACME", event=MemoryEventType.ADD),
            ],
            relations=ModifiedRelations(),
        )

        event = StoreUserMemoryEvent.from_memory_added_object(memory_added)

        assert len(event.added_memories) == 2
        assert "User likes Python" in event.added_memories
        assert "User works at ACME" in event.added_memories
        assert len(event.updated_memories) == 0
        assert len(event.deleted_memories) == 0

    def test_from_memory_added_object_with_updates(self, sample_metadata):
        """Should categorize UPDATE events correctly."""
        memory_added = MemoryAdded(
            owner_id="test_user",
            _user_id="test_user",
            _agent_id="TestAgent/test_1",
            _thread_id="thread_123",
            _display_id="display_456",
            _run_id="run_789",
            _type=MemoryType.USER_MEMORY,
            _tenant_id=None,
            _tenant_namespace=None,
            results=[
                ModifiedMemory(
                    id="mem_1",
                    memory="Updated memory",
                    event=MemoryEventType.UPDATE,
                    previous_memory="Old memory",
                ),
            ],
            relations=ModifiedRelations(),
        )

        event = StoreUserMemoryEvent.from_memory_added_object(memory_added)

        assert len(event.added_memories) == 0
        assert len(event.updated_memories) == 1
        assert event.updated_memories[0] == "Updated memory"
        assert len(event.deleted_memories) == 0

    def test_from_memory_added_object_with_deletions(self, sample_metadata):
        """Should categorize DELETE events correctly."""
        memory_added = MemoryAdded(
            owner_id="test_user",
            _user_id="test_user",
            _agent_id="TestAgent/test_1",
            _thread_id="thread_123",
            _display_id="display_456",
            _run_id="run_789",
            _type=MemoryType.USER_MEMORY,
            _tenant_id=None,
            _tenant_namespace=None,
            results=[
                ModifiedMemory(id="mem_1", memory="Deleted memory", event=MemoryEventType.DELETE),
            ],
            relations=ModifiedRelations(),
        )

        event = StoreUserMemoryEvent.from_memory_added_object(memory_added)

        assert len(event.added_memories) == 0
        assert len(event.updated_memories) == 0
        assert len(event.deleted_memories) == 1
        assert event.deleted_memories[0] == "Deleted memory"

    def test_extracts_relations(self, sample_metadata):
        """Should extract relations from MemoryAdded object."""
        memory_added = MemoryAdded(
            owner_id="test_user",
            _user_id="test_user",
            _agent_id="TestAgent/test_1",
            _thread_id="thread_123",
            _display_id="display_456",
            _run_id="run_789",
            _type=MemoryType.USER_MEMORY,
            _tenant_id=None,
            _tenant_namespace=None,
            results=[],
            relations=ModifiedRelations(
                added_entities=[
                    MemoryRelation(source="Alice", relation="works_at", target="ACME Corp"),
                ],
                deleted_entities=[
                    MemoryRelation(source="Bob", relation="lives_in", target="NYC"),
                ],
            ),
        )

        event = StoreUserMemoryEvent.from_memory_added_object(memory_added)

        assert len(event.added_relations) == 1
        assert event.added_relations[0].source == "Alice"
        assert event.added_relations[0].relation == "works_at"
        assert event.added_relations[0].target == "ACME Corp"
        assert len(event.deleted_relations) == 1
        assert event.deleted_relations[0].source == "Bob"

    def test_handles_mixed_operations(self, sample_metadata):
        """Should correctly categorize mixed ADD/UPDATE/DELETE operations."""
        memory_added = MemoryAdded(
            owner_id="test_user",
            _user_id="test_user",
            _agent_id="TestAgent/test_1",
            _thread_id="thread_123",
            _display_id="display_456",
            _run_id="run_789",
            _type=MemoryType.USER_MEMORY,
            _tenant_id=None,
            _tenant_namespace=None,
            results=[
                ModifiedMemory(id="mem_1", memory="New memory", event=MemoryEventType.ADD),
                ModifiedMemory(id="mem_2", memory="Updated memory", event=MemoryEventType.UPDATE),
                ModifiedMemory(id="mem_3", memory="Deleted memory", event=MemoryEventType.DELETE),
            ],
            relations=ModifiedRelations(),
        )

        event = StoreUserMemoryEvent.from_memory_added_object(memory_added)

        assert len(event.added_memories) == 1
        assert len(event.updated_memories) == 1
        assert len(event.deleted_memories) == 1


class TestRetrieveMemoryEvent:
    """Tests for BaseRetrieveMemoryEvent factory method."""

    @pytest.fixture
    def sample_metadata(self):
        """Sample memory metadata for tests."""
        return MemoryMetadata(
            user_id="test_user",
            agent_id="TestAgent/test_1",
            thread_id="thread_123",
            display_id="display_456",
            run_id="run_789",
            type=MemoryType.USER_MEMORY,
        )

    def test_from_memory_search_result(self, sample_metadata):
        """Should map MemorySearchResult to event correctly."""
        search_result = MemorySearchResult(
            results=[
                Memory(
                    id="1",
                    owner_id="test_user",
                    memory="User likes Python",
                    score=0.95,
                    created_at="2024-01-01T00:00:00Z",
                    metadata=sample_metadata,
                ),
                Memory(
                    id="2",
                    owner_id="test_user",
                    memory="User works at ACME",
                    score=0.87,
                    created_at="2024-01-01T00:00:00Z",
                    metadata=sample_metadata,
                ),
            ],
            relations=[
                MemoryRelation(source="Alice", relation="works_at", target="ACME"),
            ],
        )

        event = BaseRetrieveMemoryEvent.from_memory_search_result(search_result)

        assert len(event.memories) == 2
        assert event.memories[0].memory == "User likes Python"
        assert event.memories[0].score == 0.95
        assert event.memories[1].memory == "User works at ACME"
        assert len(event.relations) == 1
        assert event.relations[0].source == "Alice"

    def test_handles_empty_results(self):
        """Should handle empty search results gracefully."""
        search_result = MemorySearchResult(results=[], relations=[])

        event = BaseRetrieveMemoryEvent.from_memory_search_result(search_result)

        assert len(event.memories) == 0
        assert len(event.relations) == 0

    def test_preserves_memory_metadata(self, sample_metadata):
        """Should preserve all metadata fields from search result."""
        search_result = MemorySearchResult(
            results=[
                Memory(
                    id="1",
                    owner_id="test_user",
                    memory="Test memory",
                    score=0.95,
                    created_at="2024-01-01T00:00:00Z",
                    metadata=sample_metadata,
                ),
            ],
            relations=[],
        )

        event = BaseRetrieveMemoryEvent.from_memory_search_result(search_result)

        memory = event.memories[0]
        assert memory.metadata.user_id == "test_user"
        assert memory.metadata.agent_id == "TestAgent/test_1"
        assert memory.metadata.thread_id == "thread_123"
        assert memory.metadata.display_id == "display_456"
        assert memory.metadata.run_id == "run_789"
        assert memory.metadata.type == MemoryType.USER_MEMORY
