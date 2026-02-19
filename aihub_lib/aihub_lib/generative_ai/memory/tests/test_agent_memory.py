"""Integration tests for AgentMemory with real Mem0Service.

NOTE: These are integration tests marked with @pytest.mark.slow.
They interact with real infrastructure (Milvus, Neo4j) and are skipped by default.
Run with: uv run pytest -m slow
"""

import pytest
from llama_index.core.base.llms.types import ChatMessage, MessageRole

from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.generative_ai.memory.AgentMemory import AgentMemory
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.infrastructure.mem0.types.MemoryType import MemoryType


@pytest.fixture(scope="module")
def test_agent_config():
    """Test agent configuration."""
    return AgentConfig(
        agent_class="TestAgent",
        agent_id="test_agent_memory_1",
        name=LocaleString(en="Test Agent", de="Test Agent", fr="Agent de test", it="Agente di test"),
        description=LocaleString(
            en="Test agent for memory integration tests",
            de="Testagent für Speicherintegrationstests",
            fr="Agent de test pour les tests d'intégration de mémoire",
            it="Agente di test per test di integrazione della memoria",
        ),
    )


@pytest.fixture(scope="module")
def locale_handler():
    """Test locale handler with English locale."""
    return LocaleHandler(locale="en")


@pytest.fixture(scope="module")
def agent_memory(test_agent_config, locale_handler):
    """Agent memory instance for testing."""
    return AgentMemory(agent_config=test_agent_config, t=locale_handler)


class TestAgentMemory:
    """Integration tests for AgentMemory with real Mem0Service."""

    def test_agent_id_format(self, agent_memory):
        """Agent ID should be formatted as {agent_class}/{agent_id}."""
        assert agent_memory.agent_id == "TestAgent/test_agent_memory_1"

    def test_messages_to_dict_conversion(self, agent_memory):
        """Should convert ChatMessage list to dict format for mem0."""
        messages = [
            ChatMessage(role=MessageRole.USER, content="Hello"),
            ChatMessage(role=MessageRole.ASSISTANT, content="Hi there!"),
        ]

        result = agent_memory.messages_to_dict(messages, user_id="test_user")

        assert len(result) == 2
        assert result[0]["role"] == "user"
        assert result[0]["content"] == "Hello"
        assert result[0]["name"] == "test_user"
        assert result[1]["role"] == "assistant"
        assert result[1]["content"] == "Hi there!"
        assert result[1]["name"] == "TestAgent/test_agent_memory_1"

    def test_messages_to_dict_removes_system_messages(self, agent_memory):
        """System messages should be filtered out by default."""
        messages = [
            ChatMessage(role=MessageRole.SYSTEM, content="You are helpful"),
            ChatMessage(role=MessageRole.USER, content="Hello"),
        ]

        result = agent_memory.messages_to_dict(messages, user_id="test_user")

        assert len(result) == 1  # Only user message
        assert result[0]["role"] == "user"

    def test_messages_to_dict_keeps_system_when_specified(self, agent_memory):
        """System messages should be kept when remove_system_message=False."""
        messages = [
            ChatMessage(role=MessageRole.SYSTEM, content="You are helpful"),
            ChatMessage(role=MessageRole.USER, content="Hello"),
        ]

        result = agent_memory.messages_to_dict(messages, user_id="test_user", remove_system_message=False)

        assert len(result) == 2
        assert result[0]["role"] == "system"

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.azure
    async def test_add_user_memory_with_metadata(self, agent_memory):
        """Should preserve thread_id, display_id, run_id metadata."""
        messages = [
            ChatMessage(role=MessageRole.USER, content="I love Rust programming"),
            ChatMessage(role=MessageRole.ASSISTANT, content="That's great! Rust is a powerful systems language."),
        ]

        memory_added = await agent_memory.add_user_memory(
            messages=messages,
            user_id="test_user_memory_integration",
            thread_id="thread_123",
            display_id="display_456",
            run_id="run_789",
        )

        # Verify that EITHER memories OR relations were extracted
        # (Dual architecture: vector memories OR graph relationships)
        assert len(memory_added.results) > 0 or len(memory_added.relations.added_entities) > 0, (
            "Memory extraction should produce either vector memories (results) or graph relationships (relations)"
        )

        # Verify metadata fields are set
        assert memory_added.user_id == "test_user_memory_integration"
        assert memory_added.agent_id == "TestAgent/test_agent_memory_1"
        assert memory_added.thread_id == "thread_123"
        assert memory_added.display_id == "display_456"
        assert memory_added.run_id == "run_789"
        assert memory_added.type == MemoryType.USER_MEMORY

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.azure
    async def test_search_user_memory_returns_relevant_results(self, agent_memory):
        """Semantic search should return relevant memories."""
        # Add memory
        await agent_memory.add_user_memory(
            messages=[
                ChatMessage(role=MessageRole.USER, content="I work as a software engineer at ACME Corp"),
                ChatMessage(
                    role=MessageRole.ASSISTANT, content="Interesting! What kind of software do you work on at ACME?"
                ),
            ],
            user_id="test_user_memory_integration",
            thread_id="thread_search_1",
            display_id="display_search_1",
            run_id="run_search_1",
        )

        # Search with similar query
        result = await agent_memory.search_user_memory(
            query="What is my job?",
            user_id="test_user_memory_integration",
        )

        assert len(result.results) > 0
        # Should find something about software engineer or ACME
        memory_text = " ".join([m.memory.lower() for m in result.results])
        assert "software" in memory_text or "engineer" in memory_text or "acme" in memory_text

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.azure
    async def test_search_preserves_metadata(self, agent_memory):
        """Search should return memories with preserved metadata."""
        # Add memory with specific metadata
        await agent_memory.add_user_memory(
            messages=[
                ChatMessage(role=MessageRole.USER, content="My favorite programming language is Python"),
            ],
            user_id="test_user_memory_integration",
            thread_id="thread_meta_1",
            display_id="display_meta_1",
            run_id="run_meta_1",
        )

        # Search
        result = await agent_memory.search_user_memory(
            query="What programming language do I like?",
            user_id="test_user_memory_integration",
        )

        assert len(result.results) > 0
        memory = result.results[0]

        # Verify metadata is preserved
        assert memory.metadata.user_id == "test_user_memory_integration"
        assert memory.metadata.agent_id == "TestAgent/test_agent_memory_1"
        assert memory.metadata.type == MemoryType.USER_MEMORY

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.azure
    async def test_add_organization_memory_scoping(self, agent_memory):
        """Organization memories should be scoped to org namespace."""
        memory_added = await agent_memory.add_organization_memory(
            memory="ACME Corp uses microservices architecture",
            user_id="test_user_memory_integration",
            thread_id="thread_org_1",
            display_id="display_org_1",
            run_id="run_org_1",
            tenant_id="ACME Corp",
            tenant_namespace="acme_corp",
        )

        # Verify that EITHER memories OR relations were extracted
        # (Dual architecture: vector memories OR graph relationships)
        assert len(memory_added.results) > 0 or len(memory_added.relations.added_entities) > 0, (
            "Memory extraction should produce either vector memories (results) or graph relationships (relations)"
        )

        # Verify org scoping
        assert memory_added.owner_id == "ACME Corp"
        assert memory_added.tenant_id == "ACME Corp"
        assert memory_added.tenant_namespace == "acme_corp"
        assert memory_added.type == MemoryType.ORGANIZATION_MEMORY

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.azure
    async def test_search_organization_memory(self, agent_memory):
        """Should search organization memories correctly."""
        # Add org memory
        await agent_memory.add_organization_memory(
            memory="ACME Corp uses Docker for containerization",
            user_id="test_user_memory_integration",
            thread_id="thread_org_search_1",
            display_id="display_org_search_1",
            run_id="run_org_search_1",
            tenant_id="ACME Corp",
            tenant_namespace="acme_corp",
        )

        # Search org memories
        result = await agent_memory.search_organization_memory(
            query="What containerization technology does ACME use?",
            tenant_id="ACME Corp",
            tenant_namespace="acme_corp",
        )

        assert len(result.results) > 0
        memory_text = " ".join([m.memory.lower() for m in result.results])
        assert "docker" in memory_text or "container" in memory_text

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.azure
    async def test_user_memory_isolation(self, agent_memory):
        """User A should not see User B's memories."""
        # Add memory for user A
        await agent_memory.add_user_memory(
            messages=[ChatMessage(role=MessageRole.USER, content="User A's secret information")],
            user_id="user_a_test_isolation",
            thread_id="thread_a",
            display_id="display_a",
            run_id="run_a",
        )

        # Search as user B
        result = await agent_memory.search_user_memory(
            query="secret information",
            user_id="user_b_test_isolation",
        )

        # User B should not see User A's memory
        # (Empty result is expected - user B has no memories and shouldn't see user A's)
        if len(result.results) > 0:
            for memory in result.results:
                assert memory.metadata.user_id != "user_a_test_isolation"
