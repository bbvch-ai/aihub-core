"""Memory extraction runs LLM calls for the run, so an anonymised profile, or an anonymised run, anonymises them."""

from unittest.mock import MagicMock, patch

import pytest

from swiss_ai_hub.core.agents.agent_config import AgentConfig
from swiss_ai_hub.core.generative_ai.memory.agent_memory import AgentMemory
from swiss_ai_hub.core.generative_ai.resources.models.llm.gateway_guardrails import GatewayGuardrails
from swiss_ai_hub.core.i18n.locale_string import LocaleString

PII = GatewayGuardrails.PII_ANONYMISATION


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


def _guardrails_sent_by(anonymise: bool) -> tuple[str, ...]:
    t = MagicMock(return_value="prompt")
    t.extract.return_value = "text"
    config = AgentConfig(
        agent_id="hr", name=LocaleString(en="HR"), description=LocaleString(en="HR"), anonymise=anonymise
    )
    with patch("swiss_ai_hub.core.generative_ai.memory.agent_memory.Mem0Service") as service_cls:
        _ = AgentMemory(agent_config=config, agent_class="RAGAgent", t=t)._memory_service
    return service_cls.call_args.kwargs["requested_guardrails"]


def test_should_anonymise_extraction_when_the_profile_anonymises() -> None:
    assert _guardrails_sent_by(anonymise=True) == (PII,)


def test_should_anonymise_extraction_when_the_run_anonymises() -> None:
    with GatewayGuardrails.requesting(PII):
        assert _guardrails_sent_by(anonymise=False) == (PII,)


def test_should_not_anonymise_extraction_otherwise() -> None:
    assert _guardrails_sent_by(anonymise=False) == ()
