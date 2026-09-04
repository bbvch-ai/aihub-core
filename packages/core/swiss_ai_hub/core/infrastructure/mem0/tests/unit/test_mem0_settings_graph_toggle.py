"""Unit tests for the per-memory-type graph toggle (issues #1179, #1713).

`Mem0Settings.get_config(enable_graph=...)` controls whether the Neo4j graph store is included. mem0 keys
`enable_graph` on `graph_store.config` being truthy, so disabling must yield an empty `GraphStoreConfig`
(not None — the field is non-Optional). Both agent-facing memory scopes now opt out, but the default stays
on for the admin CRUD paths, so it must remain unchanged.
"""

from unittest.mock import MagicMock, patch

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
    """The low-level builder's `enable_graph` param still defaults to True. Both agent-facing scopes now opt
    out (#1179, #1713), but the admin CRUD paths (`UserMemory`, `OrganizationMemory`) keep the default: their
    `delete_all` is the GDPR purge, and mem0 only clears Neo4j when the service has the graph enabled."""
    assert settings.get_config().graph_store.config


def test_embedding_search_limit_uses_explicit_override(settings):
    settings.EMBEDDING_MAX_INPUT_TOKENS = 1234
    assert settings.resolved_embedding_max_input_tokens() == 1234


def test_embedding_search_limit_uses_model_info(settings):
    response = MagicMock()
    response.json.return_value = {"data": [{"model_name": "embed", "model_info": {"max_input_tokens": 1000}}]}
    with (
        patch.object(settings, "EMBEDDING_MAX_INPUT_TOKENS", None),
        patch("swiss_ai_hub.core.infrastructure.mem0.mem0_settings.LiteLLMProxySettings") as settings_cls,
    ):
        settings_cls.return_value.httpx_client.get.return_value = response
        assert settings.resolved_embedding_max_input_tokens() == 850


@pytest.mark.parametrize(
    "payload",
    [
        {"data": []},
        {"data": [{"model_name": "other", "model_info": {"max_input_tokens": 1000}}]},
        {"data": [{"model_name": "embed"}]},
        {"data": [{"model_name": "embed", "model_info": {}}]},
        {"data": [{"model_name": "embed", "model_info": {"max_input_tokens": None}}]},
        {},
    ],
)
def test_embedding_search_limit_falls_back_when_model_info_is_unavailable(settings, payload):
    response = MagicMock()
    response.json.return_value = payload
    with (
        patch.object(settings, "EMBEDDING_MAX_INPUT_TOKENS", None),
        patch("swiss_ai_hub.core.infrastructure.mem0.mem0_settings.LiteLLMProxySettings") as settings_cls,
    ):
        settings_cls.return_value.httpx_client.get.return_value = response
        assert settings.resolved_embedding_max_input_tokens() == 6963


def test_memory_search_result_relations_defaults_to_empty():
    """With the graph off, mem0 omits the `relations` key — the model must not require it."""
    assert MemorySearchResult(results=[]).relations == []
