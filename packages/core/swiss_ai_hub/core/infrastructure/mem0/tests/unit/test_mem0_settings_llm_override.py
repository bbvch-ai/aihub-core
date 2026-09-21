"""Unit tests for the per-agent extraction-model override (issue #1590).

`MEM0_LLM_NAME` is the platform default. A profile may point memory extraction at a smaller model, so
`get_config` takes an override — and must fall back to the deployment setting when none is given, so existing
profiles keep behaving exactly as before. Only the LLM moves: embedding and reranking stay global, because a
memory written with one embedder cannot be searched with another.
"""

import pytest

from swiss_ai_hub.core.infrastructure.mem0.mem0_settings import Mem0Settings

OVERRIDE_MODEL = "text-generation/small-model"


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


def test_get_config_defaults_to_the_platform_llm(settings):
    assert settings.get_config().llm.config["model"] == "llm"


def test_get_config_uses_the_override(settings):
    assert settings.get_config(llm_name=OVERRIDE_MODEL).llm.config["model"] == OVERRIDE_MODEL


def test_blank_override_falls_back_to_the_platform_llm(settings):
    """A picker submitted blank must not route extraction to an empty model name."""
    assert settings.get_config(llm_name="").llm.config["model"] == "llm"


def test_override_leaves_embedding_and_reranking_global(settings):
    config = settings.get_config(llm_name=OVERRIDE_MODEL)

    assert config.embedder.config["model"] == "embed"
    assert config.reranker.config["model"] == "rerank"


def test_override_composes_with_the_graph_toggle(settings):
    """The two options are independent; agent-facing memory always passes both."""
    config = settings.get_config(enable_graph=False, llm_name=OVERRIDE_MODEL)

    assert config.llm.config["model"] == OVERRIDE_MODEL
    assert not config.graph_store.config
