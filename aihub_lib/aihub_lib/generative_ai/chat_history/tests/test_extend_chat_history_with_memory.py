import pytest
from llama_index.core.base.llms.types import ChatMessage, MessageRole

from aihub_lib.generative_ai.chat_history.extend_chat_history_with_memory import extend_chat_history_with_memory
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.infrastructure.mem0.types.Memory import Memory
from aihub_lib.infrastructure.mem0.types.MemoryMetadata import MemoryMetadata
from aihub_lib.infrastructure.mem0.types.MemoryRelation import MemoryRelation
from aihub_lib.infrastructure.mem0.types.MemoryType import MemoryType


class TestExtendChatHistoryWithMemory:
    """Tests for memory insertion into chat history."""

    @pytest.fixture
    def t(self):
        """Default LocaleHandler with English locale."""
        return LocaleHandler(locale="en")

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

    def test_inserts_after_existing_system_messages(self, t, sample_metadata):
        """Memory message should come AFTER existing system messages."""
        chat_history = [
            ChatMessage(role=MessageRole.SYSTEM, content="You are a helpful assistant."),
            ChatMessage(role=MessageRole.SYSTEM, content="Follow these rules."),
            ChatMessage(role=MessageRole.USER, content="Hello"),
        ]
        memories = [
            Memory(
                id="1",
                owner_id="user_123",
                memory="User prefers concise answers",
                score=0.95,
                created_at="2024-01-01T00:00:00Z",
                metadata=sample_metadata,
            )
        ]

        result = extend_chat_history_with_memory(chat_history, memories, None, t)

        assert len(result) == 4
        assert result[0].role == MessageRole.SYSTEM  # Original system msg 1
        assert result[1].role == MessageRole.SYSTEM  # Original system msg 2
        assert result[2].role == MessageRole.SYSTEM  # Memory message (inserted here)
        assert "<user_context>" in result[2].content
        assert result[3].role == MessageRole.USER  # Original user message

    def test_inserts_at_beginning_if_no_system_messages(self, t, sample_metadata):
        """Memory message should be first if no existing system messages."""
        chat_history = [
            ChatMessage(role=MessageRole.USER, content="Hello"),
            ChatMessage(role=MessageRole.ASSISTANT, content="Hi!"),
        ]
        memories = [
            Memory(
                id="1",
                owner_id="user_123",
                memory="User likes Python",
                score=0.95,
                created_at="2024-01-01T00:00:00Z",
                metadata=sample_metadata,
            )
        ]

        result = extend_chat_history_with_memory(chat_history, memories, None, t)

        assert len(result) == 3
        assert result[0].role == MessageRole.SYSTEM  # Memory message inserted first
        assert result[1].role == MessageRole.USER

    def test_handles_empty_memories_list(self, t):
        """Should return unchanged history for empty memories."""
        chat_history = [ChatMessage(role=MessageRole.USER, content="Hello")]

        result = extend_chat_history_with_memory(chat_history, [], None, t)

        assert result == chat_history  # Unchanged

    def test_jinja2_template_renders_memories(self, t, sample_metadata):
        """Should render memories using Jinja2 template."""
        memories = [
            Memory(
                id="1",
                owner_id="user_123",
                memory="User likes Python",
                score=0.95,
                created_at="2024-01-01T00:00:00Z",
                metadata=sample_metadata,
            ),
            Memory(
                id="2",
                owner_id="user_123",
                memory="User works at ACME Corp",
                score=0.87,
                created_at="2024-01-01T00:00:00Z",
                metadata=sample_metadata,
            ),
        ]

        result = extend_chat_history_with_memory([], memories, None, t)

        content = result[0].content
        assert "User likes Python" in content
        assert "User works at ACME Corp" in content

    def test_jinja2_template_renders_relations(self, t, sample_metadata):
        """Should render knowledge graph relations."""
        memories = [
            Memory(
                id="1",
                owner_id="user_123",
                memory="ACME Corp",
                score=0.95,
                created_at="2024-01-01T00:00:00Z",
                metadata=sample_metadata,
            )
        ]
        relations = [
            MemoryRelation(source="Alice", relation="works_at", target="ACME Corp"),
            MemoryRelation(source="ACME Corp", relation="industry", target="Technology"),
        ]

        result = extend_chat_history_with_memory([], memories, relations, t)

        content = result[0].content
        assert "Alice works_at ACME Corp" in content
        assert "ACME Corp industry Technology" in content

    def test_locale_specific_formatting_en(self, sample_metadata):
        """English locale should use English headers."""
        t = LocaleHandler(locale="en")
        memories = [
            Memory(
                id="1",
                owner_id="user_123",
                memory="Test memory",
                score=0.95,
                created_at="2024-01-01T00:00:00Z",
                metadata=sample_metadata,
            )
        ]

        result = extend_chat_history_with_memory([], memories, None, t)

        assert "The following information has been learned" in result[0].content

    def test_locale_specific_formatting_de(self, sample_metadata):
        """German locale should use German headers."""
        t = LocaleHandler(locale="de")
        memories = [
            Memory(
                id="1",
                owner_id="user_123",
                memory="Test memory",
                score=0.95,
                created_at="2024-01-01T00:00:00Z",
                metadata=sample_metadata,
            )
        ]

        result = extend_chat_history_with_memory([], memories, None, t)

        assert "Die folgenden Informationen über den Benutzer" in result[0].content

    def test_locale_specific_formatting_fr(self, sample_metadata):
        """French locale should use French headers."""
        t = LocaleHandler(locale="fr")
        memories = [
            Memory(
                id="1",
                owner_id="user_123",
                memory="Test memory",
                score=0.95,
                created_at="2024-01-01T00:00:00Z",
                metadata=sample_metadata,
            )
        ]

        result = extend_chat_history_with_memory([], memories, None, t)

        assert "Les informations suivantes ont été apprises" in result[0].content

    def test_locale_specific_formatting_it(self, sample_metadata):
        """Italian locale should use Italian headers."""
        t = LocaleHandler(locale="it")
        memories = [
            Memory(
                id="1",
                owner_id="user_123",
                memory="Test memory",
                score=0.95,
                created_at="2024-01-01T00:00:00Z",
                metadata=sample_metadata,
            )
        ]

        result = extend_chat_history_with_memory([], memories, None, t)

        assert "Le seguenti informazioni sull'utente" in result[0].content

    def test_handles_multiple_system_messages_at_start(self, t, sample_metadata):
        """Should insert memory after the last system message when multiple exist."""
        chat_history = [
            ChatMessage(role=MessageRole.SYSTEM, content="System message 1"),
            ChatMessage(role=MessageRole.SYSTEM, content="System message 2"),
            ChatMessage(role=MessageRole.SYSTEM, content="System message 3"),
            ChatMessage(role=MessageRole.USER, content="Hello"),
        ]
        memories = [
            Memory(
                id="1",
                owner_id="user_123",
                memory="Important info",
                score=0.95,
                created_at="2024-01-01T00:00:00Z",
                metadata=sample_metadata,
            )
        ]

        result = extend_chat_history_with_memory(chat_history, memories, None, t)

        assert len(result) == 5
        # First 3 should be original system messages
        assert all(result[i].role == MessageRole.SYSTEM for i in range(4))
        # 4th system message should be memory
        assert "<user_context>" in result[3].content
        # 5th should be user message
        assert result[4].role == MessageRole.USER
