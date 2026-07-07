"""Cross-agent user-memory read routing (issue #1179).

When the user-memory graph is disabled, the vector read must take over the graph's cross-agent role by
dropping the `agent_id` partition (mirroring organization memory). When the graph is enabled, reads stay
partitioned per agent (the current per-agent memory banks). Verified at the search-call boundary.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from swiss_ai_hub.core.generative_ai.memory.agent_memory import AgentMemory


def _agent_memory(enable_graph: bool) -> AgentMemory:
    t = MagicMock(return_value="prompt")
    t.extract.return_value = "text"
    agent_config = MagicMock()
    agent_config.agent_id = "hr"
    with patch("swiss_ai_hub.core.generative_ai.memory.agent_memory.Mem0Settings") as mock_settings_cls:
        mock_settings_cls.return_value.ENABLE_USER_MEMORY_GRAPH = enable_graph
        memory = AgentMemory(agent_config=agent_config, agent_class="RAGAgent", t=t)
    # Shadow the lazily-built service so no real mem0/Milvus/Neo4j connection is needed.
    service = MagicMock()
    service.search = AsyncMock(return_value=MagicMock())
    memory._user_memory_service = service
    return memory


@pytest.mark.asyncio
async def test_graph_off_drops_agent_filter_for_cross_agent_reads():
    memory = _agent_memory(enable_graph=False)
    await memory.search_user_memory(query="q", user_id="u1")
    assert memory._user_memory_service.search.await_args.kwargs["agent_id"] is None


@pytest.mark.asyncio
async def test_graph_on_keeps_per_agent_partitioning():
    memory = _agent_memory(enable_graph=True)
    await memory.search_user_memory(query="q", user_id="u1")
    assert memory._user_memory_service.search.await_args.kwargs["agent_id"] == memory.agent_id
