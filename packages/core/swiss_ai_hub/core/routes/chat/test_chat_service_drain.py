import asyncio
from types import SimpleNamespace

from llama_index.core.base.llms.types import ChatMessage, MessageRole

from swiss_ai_hub.core.events.agent.display.chunk_event import ChunkEvent
from swiss_ai_hub.core.routes.chat.chat_service import ChatService, StreamingResources


def _streaming_resources() -> StreamingResources:
    return StreamingResources(
        stop_signal=asyncio.Event(),
        subscriber=None,
        chunk_queue=asyncio.Queue(),
        stop_event=None,
    )


def _assistant_stop_event(content: str | None) -> SimpleNamespace:
    return SimpleNamespace(
        is_hitl_request_event=False,
        output_messages=[ChatMessage(role=MessageRole.ASSISTANT, content=content)],
    )


def test_drain_yields_chunk_enqueued_after_stop_signal():
    """
    Reproduces the stop-vs-chunk dispatch race: NCSubscriber handles every message in its own task, so a
    trailing chunk's task can enqueue just after the stop task sets the signal. The drain must still yield it.
    """

    async def scenario() -> list[str]:
        resources = _streaming_resources()
        collected: list[str] = []

        async def consume() -> None:
            async for event in ChatService.iter_streamed_display_events(resources, drain_grace_seconds=0.1):
                collected.append(event.content)

        consumer = asyncio.create_task(consume())
        await asyncio.sleep(0)  # let the consumer block on the queue

        resources.stop_signal.set()  # the stop task wins the race...
        await resources.chunk_queue.put(ChunkEvent(content="trailing", model_name="m"))  # ...chunk arrives after

        await asyncio.wait_for(consumer, timeout=1.0)
        return collected

    assert asyncio.run(scenario()) == ["trailing"]


def test_drain_terminates_after_grace_when_idle():
    """With the run stopped and nothing in flight, the drain ends once the grace window elapses."""

    async def scenario() -> list[ChunkEvent]:
        resources = _streaming_resources()
        resources.stop_signal.set()
        return [event async for event in ChatService.iter_streamed_display_events(resources, drain_grace_seconds=0.02)]

    assert asyncio.run(scenario()) == []


def test_wait_for_stop_then_drain_blocks_until_stop_then_returns():
    """wait_for_stop_then_drain returns only after the stop signal is set, then waits out the grace."""

    async def scenario() -> bool:
        resources = _streaming_resources()
        drain = asyncio.create_task(ChatService.wait_for_stop_then_drain(resources, drain_grace_seconds=0.02))

        await asyncio.sleep(0.01)
        blocked_before_stop = not drain.done()

        resources.stop_signal.set()
        await asyncio.wait_for(drain, timeout=1.0)
        return blocked_before_stop

    assert asyncio.run(scenario()) is True


def test_json_backstop_recovers_answer_when_all_chunks_lost():
    """If every chunk was dropped, the JSON answer is recovered from the stop event's durable payload."""
    content = ChatService.build_json_response_content(
        chunk_events=[], stop_event=_assistant_stop_event("recovered answer")
    )

    assert content.content == "recovered answer"


def test_json_backstop_recovers_full_answer_on_partial_loss():
    """If only a prefix of the answer streamed, the JSON backstop fills in the rest from the stop event."""
    chunks = [ChunkEvent(content="full ", model_name="m")]

    content = ChatService.build_json_response_content(
        chunk_events=chunks, stop_event=_assistant_stop_event("full answer")
    )

    assert content.content == "full answer"


def test_json_keeps_streamed_chunks_when_present():
    """When every chunk streamed, the backstop stays dormant and does not duplicate the answer."""
    chunks = [ChunkEvent(content="full ", model_name="m"), ChunkEvent(content="answer", model_name="m")]

    content = ChatService.build_json_response_content(
        chunk_events=chunks, stop_event=_assistant_stop_event("full answer")
    )

    assert content.content == "full answer"


def test_json_backstop_handles_none_message_content():
    """A stop event whose message content is None must not produce a null body."""
    content = ChatService.build_json_response_content(chunk_events=[], stop_event=_assistant_stop_event(None))

    assert content.content == ""
