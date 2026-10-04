from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from llama_index.core.base.llms.types import ChatMessage, ChatResponse, MessageRole
from openai import BadRequestError

from swiss_ai_hub.core.generative_ai.guards.text_verdict import request_verdict_for_messages
from swiss_ai_hub.core.generative_ai.resources.models.llm.reasoning_free_chat import ReasoningFreeChat
from swiss_ai_hub.core.generative_ai.retrieval.condense_standalone_question import condense_standalone_question

QUESTION = [ChatMessage(role=MessageRole.USER, content="Is the context sufficient?")]
THINKING_OFF = {"chat_template_kwargs": {"thinking": False, "enable_thinking": False}}


def _llm(*replies: object) -> MagicMock:
    llm = MagicMock()
    llm.achat = AsyncMock(side_effect=list(replies))
    return llm


def _reply(content: str) -> ChatResponse:
    return ChatResponse(message=ChatMessage(role=MessageRole.ASSISTANT, content=content))


def _bad_request() -> BadRequestError:
    request = httpx.Request("POST", "http://litellm/v1/chat/completions")
    return BadRequestError("chat_template is not supported", response=httpx.Response(400, request=request), body=None)


@pytest.mark.asyncio
async def test_switches_thinking_off_under_every_key_a_reasoning_model_reads():
    llm = _llm(_reply("SUFFICIENT"))

    await ReasoningFreeChat.achat(llm, QUESTION)

    assert llm.achat.await_args.kwargs["extra_body"] == THINKING_OFF


@pytest.mark.asyncio
async def test_a_model_rejecting_the_switch_gets_a_plain_request():
    llm = _llm(_bad_request(), _reply("SUFFICIENT"))

    response = await ReasoningFreeChat.achat(llm, QUESTION)

    assert response.message.content == "SUFFICIENT"
    assert "extra_body" not in llm.achat.await_args.kwargs


@pytest.mark.asyncio
async def test_guard_verdicts_are_asked_with_thinking_off():
    llm = _llm(_reply("SUFFICIENT"))

    await request_verdict_for_messages(llm, QUESTION)

    assert llm.achat.await_args.kwargs["extra_body"] == THINKING_OFF


@pytest.mark.asyncio
async def test_the_question_is_condensed_with_thinking_off():
    llm = _llm(_reply("What is the reach of the AR-7?"))
    t = MagicMock(return_value="Rewrite the question using {chat_history}")

    await condense_standalone_question(ChatMessage(role=MessageRole.USER, content="And its reach?"), [], t, llm)

    assert llm.achat.await_args.kwargs["extra_body"] == THINKING_OFF
