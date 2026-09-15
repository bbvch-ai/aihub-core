"""`AgentMemory` extracts on the profile's own model when one is configured (issue #1590).

Asserted on the config handed to `Mem0Service` rather than on a live client, since constructing one would
reach for Milvus. The fallback is a deployment setting (`MEM0_LLM_NAME`), not a sibling config field, which is
why resolution lives here instead of in a config validator.
"""

from unittest.mock import MagicMock, patch

import pytest

from swiss_ai_hub.core.generative_ai.memory.agent_memory import AgentMemory

OVERRIDE_MODEL = "text-generation/small-model"


@pytest.fixture(autouse=True)
def mem0_env(monkeypatch) -> None:
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


def _agent_memory(llm_model_name: str | None) -> AgentMemory:
    t = MagicMock(return_value="prompt")
    t.extract.return_value = "text"
    agent_config = MagicMock()
    agent_config.agent_id = "hr"
    return AgentMemory(agent_config=agent_config, agent_class="RAGAgent", t=t, llm_model_name=llm_model_name)


def _extraction_model_of(memory: AgentMemory) -> str:
    with patch("swiss_ai_hub.core.generative_ai.memory.agent_memory.Mem0Service") as service_cls:
        _ = memory._memory_service
    return service_cls.call_args.args[0].llm.config["model"]


def test_falls_back_to_the_platform_model_when_unconfigured():
    """Existing profiles carry no memory model and must keep extracting exactly as before."""
    assert _extraction_model_of(_agent_memory(None)) == "llm"


def test_uses_the_configured_model():
    assert _extraction_model_of(_agent_memory(OVERRIDE_MODEL)) == OVERRIDE_MODEL


def test_the_override_is_optional_for_callers():
    """The dispatcher and the memory writer pass it; playground and admin call sites do not."""
    t = MagicMock(return_value="prompt")
    t.extract.return_value = "text"

    memory = AgentMemory(agent_config=MagicMock(), agent_class="RAGAgent", t=t)

    assert _extraction_model_of(memory) == "llm"
