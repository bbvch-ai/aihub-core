import json
from unittest.mock import Mock, patch

import pytest
from fastapi import HTTPException
from swiss_ai_hub.core.events.agent import ChunkEvent, StopEvent

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
