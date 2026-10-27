"""The guardrails requested for the current task reach the gateway in the body of every request the client sends."""

import json

import httpx
import pytest
from llama_index.core.base.llms.types import ChatMessage, MessageRole

from swiss_ai_hub.core.generative_ai.resources.models.llm.gateway_guardrails import GatewayGuardrails
from swiss_ai_hub.core.generative_ai.resources.models.llm.reasoning_free_chat import ReasoningFreeChat
from swiss_ai_hub.core.generative_ai.resources.models.llm.resilient_open_ai_like import ResilientOpenAILike

PII = GatewayGuardrails.PII_ANONYMISATION
COMPLETION = {
    "id": "c",
    "object": "chat.completion",
    "created": 0,
    "model": "m",
    "choices": [{"index": 0, "message": {"role": "assistant", "content": "ok"}, "finish_reason": "stop"}],
    "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
}
MESSAGES = [ChatMessage(role=MessageRole.USER, content="Patient Reto Wyss")]


def _llm(sent: list[dict]) -> ResilientOpenAILike:
    def answer(request: httpx.Request) -> httpx.Response:
        sent.append(json.loads(request.content))
        return httpx.Response(200, json=COMPLETION)

    transport = httpx.MockTransport(answer)
    return ResilientOpenAILike(
        model="text-generation/gemma-4-31B-it",
        api_base="http://litellm/v1",
        api_key="test",
        is_chat_model=True,
        connect_timeout=5.0,
        http_client=httpx.Client(transport=transport),
        async_http_client=httpx.AsyncClient(transport=transport),
    )


@pytest.mark.asyncio
async def test_should_request_the_guardrail_when_the_task_anonymises() -> None:
    sent: list[dict] = []

    with GatewayGuardrails.requesting(PII):
        await _llm(sent).achat(MESSAGES)

    assert sent[0]["guardrails"] == [PII]


@pytest.mark.asyncio
async def test_should_request_no_guardrail_when_the_task_does_not_anonymise() -> None:
    sent: list[dict] = []

    await _llm(sent).achat(MESSAGES)

    assert "guardrails" not in sent[0]


def test_should_request_the_guardrail_on_sync_calls_too() -> None:
    sent: list[dict] = []

    with GatewayGuardrails.requesting(PII):
        _llm(sent).chat(MESSAGES)

    assert sent[0]["guardrails"] == [PII]


@pytest.mark.asyncio
async def test_should_keep_the_reasoning_switch_of_a_side_call_next_to_the_guardrail() -> None:
    sent: list[dict] = []

    with GatewayGuardrails.requesting(PII):
        await ReasoningFreeChat.achat(_llm(sent), MESSAGES)

    assert sent[0]["guardrails"] == [PII]
    assert sent[0]["chat_template_kwargs"] == ReasoningFreeChat.EXTRA_BODY["chat_template_kwargs"]
