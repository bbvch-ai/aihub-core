import asyncio
from collections.abc import AsyncIterator
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from llama_index.core.base.llms.types import ChatMessage, MessageRole

from swiss_ai_hub.core.displayers.event_displayer import EventDisplayer
from swiss_ai_hub.core.events.agent.display.chunk_event import ChunkEvent
from swiss_ai_hub.core.events.agent.semantic.llm.llm_event import LLMEvent
from swiss_ai_hub.core.events.agent.semantic.llm.llm_stop_event import LLMStopEvent


@pytest.fixture
def publisher():
    return AsyncMock()


@pytest.fixture
def topic_manager():
    manager = Mock()
    manager.get_subject_for_display_event_in_thread.return_value = "agent.test.display.subject"
    return manager


@pytest.fixture
def displayer(publisher, topic_manager):
    return EventDisplayer(publisher=publisher, topic_manager=topic_manager)


@pytest.fixture
def llm_config():
    config = Mock()
    config.model_name = "test-model"
    config.model_dump.return_value = {"model_name": "test-model"}
    return config


def make_llm(deltas: list[str], delay_between_chunks: float = 0.0) -> Mock:
    """Fake LLM exposing only `astream_chat`, the API `display_llm_stream` must drive."""

    async def astream_chat(messages: list[ChatMessage]) -> AsyncIterator[SimpleNamespace]:
        async def gen() -> AsyncIterator[SimpleNamespace]:
            for delta in deltas:
                if delay_between_chunks:
                    await asyncio.sleep(delay_between_chunks)
                yield SimpleNamespace(delta=delta)

        return gen()

    llm = Mock()
    llm.astream_chat = astream_chat
    llm.callback_manager.handlers = []
    return llm


def published_chunk_contents(publisher: AsyncMock) -> str:
    events = [call.args[0] for call in publisher.publish_event.call_args_list]
    return "".join(event.content for event in events if isinstance(event, ChunkEvent))


@pytest.mark.asyncio
async def test_display_llm_stream_streams_chunks_and_returns_llm_event(displayer, publisher, llm_config):
    deltas = ["Hello ", "world.", " How are you?"]
    llm = make_llm(deltas)
    messages = [ChatMessage(role=MessageRole.USER, content="hi")]

    result = await displayer.display_llm_stream(llm_config, llm, messages)

    assert isinstance(result, LLMEvent)
    assert not isinstance(result, LLMStopEvent)
    assert result.output_messages[0].content == "Hello world. How are you?"
    assert result.chat_model_name == "test-model"
    assert published_chunk_contents(publisher) == "Hello world. How are you?"


@pytest.mark.asyncio
async def test_display_llm_stream_as_stop_step_returns_stop_event(displayer, llm_config):
    llm = make_llm(["Done."])
    messages = [ChatMessage(role=MessageRole.USER, content="hi")]

    result = await displayer.display_llm_stream(llm_config, llm, messages, as_stop_step=True)

    assert isinstance(result, LLMStopEvent)
    assert result.output_messages[0].content == "Done."


@pytest.mark.asyncio
async def test_display_llm_stream_does_not_block_event_loop(displayer, llm_config):
    """
    Regression test for #1631: a slow LLM stream must yield control between chunks so the
    runner keeps servicing discovery requests, NATS acks, and other runs while streaming.
    """
    llm = make_llm(["one. ", "two. ", "three. ", "four."], delay_between_chunks=0.05)
    messages = [ChatMessage(role=MessageRole.USER, content="hi")]

    heartbeats = 0

    async def heartbeat():
        nonlocal heartbeats
        while True:
            await asyncio.sleep(0.01)
            heartbeats += 1

    heartbeat_task = asyncio.create_task(heartbeat())
    try:
        await displayer.display_llm_stream(llm_config, llm, messages)
    finally:
        heartbeat_task.cancel()

    assert heartbeats >= 5


@pytest.mark.asyncio
async def test_concurrent_streams_interleave(displayer, llm_config):
    """Two concurrent runs on one agent must stream independently instead of serialising."""
    slow_llm = make_llm(["slow-a. ", "slow-b."], delay_between_chunks=0.5)
    fast_llm = make_llm(["fast."])
    messages = [ChatMessage(role=MessageRole.USER, content="hi")]

    slow_task = asyncio.create_task(displayer.display_llm_stream(llm_config, slow_llm, messages))
    await asyncio.sleep(0.01)
    fast_result = await asyncio.wait_for(displayer.display_llm_stream(llm_config, fast_llm, messages), timeout=0.4)

    assert fast_result.output_messages[0].content == "fast."
    slow_result = await slow_task
    assert slow_result.output_messages[0].content == "slow-a. slow-b."
