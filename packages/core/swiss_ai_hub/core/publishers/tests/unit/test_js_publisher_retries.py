"""A publish the broker refuses for its size fails at once; a timeout is still retried.

Retrying an oversized event resent the same bytes ten times a second apart, and each attempt left a pending JetStream
future behind, before the caller could end the run."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from nats.errors import MaxPayloadError

from swiss_ai_hub.core.events.base_event import BaseEvent
from swiss_ai_hub.core.publishers.js_publisher import JSPublisher

SUBJECT = "agent.MyAgent.profile.thread.display.run.controlEvent.BaseEvent.eid"


def _publisher(publish_async: AsyncMock) -> JSPublisher:
    js = MagicMock()
    js.publish_async = publish_async
    publisher = JSPublisher(name="test", js=js)
    publisher._ensured_streams.add("anything")
    return publisher


def _timing_out_once() -> AsyncMock:
    attempts: list[int] = []

    async def publish_async(*_args, **_kwargs) -> asyncio.Future:
        attempts.append(1)
        if len(attempts) == 1:
            raise TimeoutError
        ack = asyncio.Future()
        ack.set_result(MagicMock(seq=1, stream="test-stream"))
        return ack

    return AsyncMock(side_effect=publish_async)


@pytest.mark.asyncio
async def test_an_event_above_the_payload_limit_fails_without_retrying():
    publish_async = AsyncMock(side_effect=MaxPayloadError)

    with patch("swiss_ai_hub.core.publishers.js_publisher.asyncio.sleep", new=AsyncMock()) as sleep:
        with pytest.raises(MaxPayloadError):
            await _publisher(publish_async).publish_event(BaseEvent(), SUBJECT)

    assert publish_async.await_count == 1
    sleep.assert_not_awaited()


@pytest.mark.asyncio
async def test_a_timeout_is_still_retried():
    publish_async = _timing_out_once()

    with patch("swiss_ai_hub.core.publishers.js_publisher.asyncio.sleep", new=AsyncMock()):
        await _publisher(publish_async).publish_event(BaseEvent(), SUBJECT)

    assert publish_async.await_count == 2
