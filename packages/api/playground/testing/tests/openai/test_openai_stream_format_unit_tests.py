import json
from unittest.mock import Mock, patch

import pytest
from fastapi import HTTPException
from swiss_ai_hub.core.events.agent import ChunkEvent, ExceptionEvent, StopEvent
from swiss_ai_hub.core.generative_ai import LLMCosts

from swiss_ai_hub.api.routes.openai.openai_service import OpenaiService

_SERVICE = "swiss_ai_hub.api.routes.openai.openai_service"


async def _agent_stream(contents: list[str]) -> list[str]:
    async def events(_resources):
        for content in contents:
            yield ChunkEvent(content=content, model_name="text-generation/some-llm")

    resources = Mock(stop_event=StopEvent())
    with patch(f"{_SERVICE}.ChatService.iter_streamed_display_events", events):
        return [line async for line in OpenaiService._sse_event_generator(resources, model="UniversalAgent/assistant")]


def _chunks(lines: list[str]) -> list[dict]:
    return [json.loads(line.removeprefix("data: ")) for line in lines if line != OpenaiService.STREAM_END]


@pytest.mark.asyncio
async def test_an_agent_stream_ends_with_done():
    lines = await _agent_stream(["Hello", " world"])
    assert lines[-1] == "data: [DONE]\n\n"


@pytest.mark.asyncio
async def test_every_chunk_of_an_agent_answer_shares_id_creation_time_and_the_agent_as_model():
    chunks = _chunks(await _agent_stream(["Hello", " world"]))

    assert len({chunk["id"] for chunk in chunks}) == 1
    assert chunks[0]["id"].startswith("chatcmpl-")
    assert len({chunk["created"] for chunk in chunks}) == 1
    assert {chunk["model"] for chunk in chunks} == {"UniversalAgent/assistant"}


@pytest.mark.asyncio
async def test_only_the_first_delta_carries_the_role():
    chunks = _chunks(await _agent_stream(["Hello", " world"]))

    assert [chunk["choices"][0]["delta"].get("role") for chunk in chunks] == ["assistant", None, None]
    assert chunks[-1]["choices"][0]["finish_reason"] == "stop"


@pytest.mark.asyncio
async def test_an_answer_streamed_in_one_final_chunk_still_carries_the_role():
    chunks = _chunks(await _agent_stream([]))
    assert chunks[0]["choices"][0]["delta"]["role"] == "assistant"


@pytest.mark.parametrize("model_name", ["gpt-4o", "/assistant", "UniversalAgent/", "a/b/c"])
def test_a_name_that_is_neither_model_nor_agent_is_not_found(model_name: str):
    with pytest.raises(HTTPException) as not_found:
        OpenaiService._agent_of(model_name)
    assert not_found.value.status_code == 404


def test_an_agent_name_splits_into_class_and_id():
    assert OpenaiService._agent_of("UniversalAgent/assistant") == ("UniversalAgent", "assistant")


async def _agent_stream_ending_with(stop_event, *, include_usage: bool = False, costs=None) -> list[str]:
    async def events(_resources):
        yield ChunkEvent(content="Partial", model_name="text-generation/some-llm")

    resources = Mock(stop_event=stop_event, costs=costs)
    with patch(f"{_SERVICE}.ChatService.iter_streamed_display_events", events):
        return [
            line
            async for line in OpenaiService._sse_event_generator(
                resources, model="UniversalAgent/assistant", include_usage=include_usage
            )
        ]


@pytest.mark.asyncio
async def test_a_failing_agent_ends_the_stream_with_an_error_event():
    lines = await _agent_stream_ending_with(ExceptionEvent(message="Knowledge base unreachable", http_status_code=503))

    error = json.loads(lines[-2].removeprefix("data: "))
    assert error["error"]["message"] == "Knowledge base unreachable"
    assert error["error"]["code"] == 503
    assert lines[-1] == OpenaiService.STREAM_END
    assert not any("CAUTION" in line for line in lines)


@pytest.mark.asyncio
async def test_usage_is_sent_last_when_asked_for():
    costs = LLMCosts.from_zero().model_copy(update={"prompt_token_count": 120, "completion_token_count": 30})
    lines = await _agent_stream_ending_with(StopEvent(), include_usage=True, costs=costs)

    usage_chunk = json.loads(lines[-2].removeprefix("data: "))
    assert usage_chunk["choices"] == []
    assert usage_chunk["usage"] == {"prompt_tokens": 120, "completion_tokens": 30, "total_tokens": 150} | {
        key: usage_chunk["usage"][key] for key in usage_chunk["usage"] if key.endswith("_details")
    }


@pytest.mark.asyncio
async def test_no_usage_chunk_unless_asked_for():
    chunks = _chunks(await _agent_stream_ending_with(StopEvent()))
    assert all(chunk["choices"] for chunk in chunks)
