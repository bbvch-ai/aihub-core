"""Cross-agent user-memory read routing (issue #1179).

User memory runs without the graph store, so the vector read takes over the graph's former cross-agent role:
`search_user_memory` must NOT partition by `agent_id`, returning all of a user's memories regardless of which
agent wrote them (mirroring organization memory). Verified at the search-call boundary.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from swiss_ai_hub.core.generative_ai.memory.agent_memory import AgentMemory


def _agent_memory() -> AgentMemory:
    t = MagicMock(return_value="prompt")
    t.extract.return_value = "text"
    agent_config = MagicMock()
    agent_config.agent_id = "hr"
    with patch("swiss_ai_hub.core.generative_ai.memory.agent_memory.Mem0Settings"):
        memory = AgentMemory(agent_config=agent_config, agent_class="RAGAgent", t=t)
    # Shadow the lazily-built service so no real mem0/Milvus/Neo4j connection is needed.
    service = MagicMock()
    service.search = AsyncMock(return_value=MagicMock())
    memory._memory_service = service
    return memory


@pytest.mark.asyncio
async def test_user_memory_read_is_cross_agent():
    memory = _agent_memory()
    await memory.search_user_memory(query="q", user_id="u1")
    assert memory._memory_service.search.await_args.kwargs["agent_id"] is None
