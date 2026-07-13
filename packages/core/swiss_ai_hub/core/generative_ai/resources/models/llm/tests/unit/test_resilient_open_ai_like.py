from unittest.mock import AsyncMock, patch

import httpx
import pytest
from llama_index.llms.openai_like import OpenAILike
from openai import BadRequestError
from pydantic import BaseModel, ValidationError

from swiss_ai_hub.core.generative_ai.resources.models.llm.resilient_open_ai_like import ResilientOpenAILike


class _Result(BaseModel):
    value: str


def _bad_request() -> BadRequestError:
    request = httpx.Request("POST", "http://litellm/v1/chat/completions")
    response = httpx.Response(400, request=request, text="chat_template is not supported")
    return BadRequestError("chat_template is not supported", response=response, body=None)


def _llm(*, structured: bool) -> ResilientOpenAILike:
    return ResilientOpenAILike(
        model="text-generation/Kimi-K2.6",
        api_base="http://litellm/v1",
        api_key="test",
        should_use_structured_outputs=structured,
    )


@pytest.mark.asyncio
async def test_structured_output_path_disables_reasoning():
    llm = _llm(structured=True)
    with patch.object(OpenAILike, "astructured_predict", new=AsyncMock(return_value=_Result(value="ok"))) as parent:
        await llm.astructured_predict(_Result, "prompt")

    forwarded = parent.await_args.kwargs["llm_kwargs"]
    assert forwarded["extra_body"] == {"chat_template_kwargs": {"thinking": False}}


@pytest.mark.asyncio
async def test_falls_back_to_plain_request_when_chat_template_rejected():
    llm = _llm(structured=True)
    parent = AsyncMock(side_effect=[_bad_request(), _Result(value="ok")])
    with patch.object(OpenAILike, "astructured_predict", new=parent):
        result = await llm.astructured_predict(_Result, "prompt")

    assert result.value == "ok"
    assert parent.await_count == 2
    assert "extra_body" in parent.await_args_list[0].kwargs["llm_kwargs"]
    assert "extra_body" not in (parent.await_args_list[1].kwargs.get("llm_kwargs") or {})


@pytest.mark.asyncio
async def test_no_reasoning_disable_when_capability_not_declared():
    llm = _llm(structured=False)
    with patch.object(OpenAILike, "astructured_predict", new=AsyncMock(return_value=_Result(value="ok"))) as parent:
        await llm.astructured_predict(_Result, "prompt")

    assert "extra_body" not in (parent.await_args.kwargs.get("llm_kwargs") or {})


@pytest.mark.asyncio
async def test_retries_malformed_output_then_succeeds():
    llm = _llm(structured=True)
    parent = AsyncMock(side_effect=[ValidationError.from_exception_data("x", []), _Result(value="ok")])
    with patch.object(OpenAILike, "astructured_predict", new=parent):
        result = await llm.astructured_predict(_Result, "prompt")

    assert result.value == "ok"
    assert parent.await_count == 2
