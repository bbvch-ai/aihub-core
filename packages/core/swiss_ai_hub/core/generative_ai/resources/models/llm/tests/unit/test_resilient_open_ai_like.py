from collections.abc import AsyncIterator, Sequence
from typing import Any
from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest
from llama_index.core.base.llms.types import ChatMessage, ChatResponse, MessageRole
from llama_index.llms.openai_like import OpenAILike
from openai import BadRequestError
from pydantic import BaseModel, ValidationError

from swiss_ai_hub.core.generative_ai.resources.models.llm.resilient_open_ai_like import ResilientOpenAILike


class _Result(BaseModel):
    value: str


def _bad_request(detail: str = "chat_template is not supported") -> BadRequestError:
    request = httpx.Request("POST", "http://litellm/v1/chat/completions")
    response = httpx.Response(400, request=request, text=detail)
    return BadRequestError(detail, response=response, body=None)


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
    assert forwarded["extra_body"] == {"chat_template_kwargs": {"thinking": False, "enable_thinking": False}}


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


_STREAM_OPTIONS_REJECTED = "stream_options is not supported by this endpoint"


@pytest.fixture(autouse=True)
def forget_rejecting_models():
    """The rejection memo is process-wide, so one test's fallback must not leak into the next."""
    ResilientOpenAILike._models_rejecting_stream_options.clear()
    yield
    ResilientOpenAILike._models_rejecting_stream_options.clear()


def _messages() -> Sequence[ChatMessage]:
    return [ChatMessage(role=MessageRole.USER, content="hi")]


async def _chunks(deltas: list[str], fail_at: int | None = None) -> AsyncIterator[ChatResponse]:
    """Fake upstream stream; a 400 raised at ``fail_at`` mimics the endpoint refusing mid-iteration."""
    for index, delta in enumerate(deltas):
        if index == fail_at:
            raise _bad_request(_STREAM_OPTIONS_REJECTED)
        yield ChatResponse(message=ChatMessage(role=MessageRole.ASSISTANT, content=delta), delta=delta)


def _streams(*upstreams: AsyncIterator[ChatResponse]) -> AsyncMock:
    return AsyncMock(side_effect=list(upstreams))


async def _collect(stream: Any) -> list[str]:
    return [chunk.delta async for chunk in stream]


@pytest.mark.asyncio
async def test_streaming_asks_the_gateway_for_usage_on_the_final_chunk():
    llm = _llm(structured=False)
    parent = _streams(_chunks(["Bern."]))

    with patch.object(OpenAILike, "astream_chat", new=parent):
        deltas = await _collect(await llm.astream_chat(_messages()))

    assert deltas == ["Bern."]
    assert parent.await_args.kwargs["stream_options"] == {"include_usage": True}


@pytest.mark.asyncio
async def test_falls_back_to_a_plain_stream_when_stream_options_rejected():
    llm = _llm(structured=False)
    parent = _streams(_chunks(["Bern."], fail_at=0), _chunks(["Bern."]))

    with patch.object(OpenAILike, "astream_chat", new=parent):
        deltas = await _collect(await llm.astream_chat(_messages()))

    assert deltas == ["Bern."]
    assert parent.await_count == 2
    assert "stream_options" not in parent.await_args_list[1].kwargs


@pytest.mark.asyncio
async def test_a_rejecting_model_is_not_asked_for_usage_again():
    llm = _llm(structured=False)
    parent = _streams(_chunks(["one"], fail_at=0), _chunks(["one"]), _chunks(["two"]))

    with patch.object(OpenAILike, "astream_chat", new=parent):
        await _collect(await llm.astream_chat(_messages()))
        await _collect(await llm.astream_chat(_messages()))

    assert parent.await_count == 3
    assert "stream_options" not in parent.await_args_list[2].kwargs


@pytest.mark.asyncio
async def test_a_rejection_after_the_first_chunk_is_not_retried():
    """Retrying once output has been streamed would replay the already-displayed chunks."""
    llm = _llm(structured=False)
    parent = _streams(_chunks(["Be", "rn."], fail_at=1), _chunks(["Be", "rn."]))

    with patch.object(OpenAILike, "astream_chat", new=parent), pytest.raises(BadRequestError):
        await _collect(await llm.astream_chat(_messages()))

    assert parent.await_count == 1


def test_the_synchronous_stream_falls_back_the_same_way():
    llm = _llm(structured=False)

    def chunks(deltas: list[str], fail_at: int | None = None):
        for index, delta in enumerate(deltas):
            if index == fail_at:
                raise _bad_request(_STREAM_OPTIONS_REJECTED)
            yield ChatResponse(message=ChatMessage(role=MessageRole.ASSISTANT, content=delta), delta=delta)

    parent = Mock(side_effect=[chunks(["Bern."], fail_at=0), chunks(["Bern."])])
    with patch.object(OpenAILike, "stream_chat", new=parent):
        deltas = [chunk.delta for chunk in llm.stream_chat(_messages())]

    assert deltas == ["Bern."]
    assert parent.call_count == 2
    assert "stream_options" not in parent.call_args_list[1].kwargs
