"""Unit tests for the per-memory-type graph toggle (issue #1179).

`Mem0Settings.get_config(enable_graph=...)` controls whether the Neo4j graph store is included. mem0 keys
`enable_graph` on `graph_store.config` being truthy, so disabling must yield an empty `GraphStoreConfig`
(not None — the field is non-Optional). Default behavior (graph on) must be unchanged.
"""

import pytest

from swiss_ai_hub.core.infrastructure.mem0.mem0_settings import Mem0Settings
from swiss_ai_hub.core.infrastructure.mem0.types.memory_search_result import MemorySearchResult


@pytest.fixture
def settings(monkeypatch) -> Mem0Settings:
    """Mem0Settings with the env the sub-settings (LiteLLM/Milvus/Neo4j) require to build a config."""
    monkeypatch.setenv("LITE_LLM_PROXY_BASE_URL", "http://litellm:4000")
    monkeypatch.setenv("LITE_LLM_PROXY_API_KEY", "test-key")
    monkeypatch.setenv("MILVUS_URL", "http://milvus:19530")
    monkeypatch.setenv("MILVUS_DIMENSION", "1024")
    monkeypatch.setenv("MILVUS_ROOT_PASSWORD", "test-pw")
    monkeypatch.setenv("NEO4J_URL", "bolt://neo4j:7687")
    monkeypatch.setenv("NEO4J_USERNAME", "neo4j")
    monkeypatch.setenv("NEO4J_PASSWORD", "test-pw")
    return Mem0Settings(LLM_NAME="llm", EMBEDDING_MODEL_NAME="embed", RERANKING_MODEL_NAME="rerank")


def test_enable_graph_true_includes_neo4j_store(settings):
    config = settings.get_config(enable_graph=True)
    assert config.graph_store.config  # truthy → mem0 sets enable_graph=True
    assert config.graph_store.provider == "neo4j"


def test_enable_graph_false_yields_empty_graph_store(settings):
    config = settings.get_config(enable_graph=False)
    # Empty config → mem0 treats the graph as disabled and skips the graph branch.
    assert not config.graph_store.config


def test_get_config_defaults_to_graph_on(settings):
    """The low-level builder's `enable_graph` param still defaults to True (org memory relies on it)."""
    assert settings.get_config().graph_store.config


def test_memory_search_result_relations_defaults_to_empty():
    """With the graph off, mem0 omits the `relations` key — the model must not require it."""
    assert MemorySearchResult(results=[]).relations == []
