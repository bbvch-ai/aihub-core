"""Agent-facing memory opens no Neo4j connection (issues #1179, #1713).

Both scopes share one graph-free `Mem0Service`. Asserted on the config handed to `Mem0Service` rather than
on a live client, since constructing one would reach for Milvus. Without this, restoring the graph — which
the superseded half of ADR `2026_07_07` argued for — reintroduces the ~1.9s per-message read cost silently.
"""

from unittest.mock import MagicMock, patch

import pytest

from swiss_ai_hub.core.generative_ai.memory.agent_memory import AgentMemory


@pytest.fixture
def agent_memory(monkeypatch) -> AgentMemory:
    monkeypatch.setenv("LITE_LLM_PROXY_BASE_URL", "http://litellm:4000")
    monkeypatch.setenv("LITE_LLM_PROXY_API_KEY", "test-key")
    monkeypatch.setenv("MILVUS_URL", "http://milvus:19530")
    monkeypatch.setenv("MILVUS_DIMENSION", "1024")
    monkeypatch.setenv("MILVUS_ROOT_PASSWORD", "test-pw")
    monkeypatch.setenv("NEO4J_URL", "bolt://neo4j:7687")
    monkeypatch.setenv("NEO4J_USERNAME", "neo4j")
    monkeypatch.setenv("NEO4J_PASSWORD", "test-pw")
    monkeypatch.setenv("MEM0_LLM_NAME", "llm")
    monkeypatch.setenv("MEM0_EMBEDDING_MODEL_NAME", "embed")
    monkeypatch.setenv("MEM0_RERANKING_MODEL_NAME", "rerank")

    t = MagicMock(return_value="prompt")
    t.extract.return_value = "text"
    agent_config = MagicMock()
    agent_config.agent_id = "hr"
    return AgentMemory(agent_config=agent_config, agent_class="RAGAgent", t=t)


def test_memory_service_is_built_without_the_graph_store(agent_memory):
    with patch("swiss_ai_hub.core.generative_ai.memory.agent_memory.Mem0Service") as service_cls:
        _ = agent_memory._memory_service

    config = service_cls.call_args.args[0]
    # Falsy graph_store.config is how mem0 keys enable_graph off — see Mem0Settings.get_config.
    assert not config.graph_store.config
