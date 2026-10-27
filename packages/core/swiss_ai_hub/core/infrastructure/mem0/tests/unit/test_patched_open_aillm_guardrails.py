"""mem0's extraction calls run on its own worker threads, so they carry the guardrails set on the instance."""

from types import SimpleNamespace
from unittest.mock import MagicMock

from mem0.llms.openai import OpenAILLM

from swiss_ai_hub.core.generative_ai.resources.models.llm.gateway_guardrails import GatewayGuardrails
from swiss_ai_hub.core.infrastructure.mem0.patched_open_aillm import PatchedOpenAILLM

PII = GatewayGuardrails.PII_ANONYMISATION


def _llm(model: str = "text-generation/gemma-4-31B-it") -> tuple[PatchedOpenAILLM, MagicMock]:
    llm = PatchedOpenAILLM.from_llm(OpenAILLM({"model": model, "api_key": "k", "openai_base_url": "http://x"}))
    create = MagicMock(
        return_value=SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content='{"facts": []}'))])
    )
    llm.client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    return llm, create


def test_should_request_the_guardrail_on_extraction_calls_when_set() -> None:
    llm, create = _llm()
    llm.requested_guardrails = (PII,)

    llm.generate_response(messages=[{"role": "user", "content": "Reto Wyss"}])

    assert create.call_args.kwargs["extra_body"] == {"guardrails": [PII]}


def test_should_request_it_for_reasoning_models_whose_params_mem0_filters() -> None:
    llm, create = _llm(model="o3-mini")
    llm.requested_guardrails = (PII,)

    llm.generate_response(messages=[{"role": "user", "content": "Reto Wyss"}])

    assert create.call_args.kwargs["extra_body"] == {"guardrails": [PII]}


def test_should_request_no_guardrail_by_default() -> None:
    llm, create = _llm()

    llm.generate_response(messages=[{"role": "user", "content": "Reto Wyss"}])

    assert "extra_body" not in create.call_args.kwargs
