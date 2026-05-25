"""Lock the publisher builder-chain order so a future reorder cannot silently drop X-AIHub-* or
clobber the trace-context / Nats-Msg-Id headers. The helper itself (``with_aihub_headers``) is
exhaustively tested in
``packages/core/swiss_ai_hub/core/tracing/tests/unit/test_nats_message_headers.py`` — these tests
only exist to pin its integration through the publisher chains."""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from swiss_ai_hub.core.events.base_event import BaseEvent
from swiss_ai_hub.core.publishers.js_publisher import JSPublisher
from swiss_ai_hub.core.publishers.nc_publisher import NCPublisher


@pytest.mark.asyncio
async def test_js_publisher_threads_extra_headers_into_published_message():
    """``JSPublisher.publish_event(..., extra_headers=...)`` must merge X-AIHub-* values onto the
    published NATS headers without clobbering ``Nats-Msg-Id`` (set earlier in the chain)."""
    js = MagicMock()

    async def publish_async(*_args, **_kwargs):
        inner = asyncio.Future()
        inner.set_result(MagicMock(seq=1, stream="test-stream"))
        return inner

    js.publish_async = AsyncMock(side_effect=publish_async)

    publisher = JSPublisher(name="test", js=js)
    publisher._ensured_streams.add("anything")  # skip stream creation

    await publisher.publish_event(
        BaseEvent(),
        "agent.MyAgent.profile.thread.display.run.controlEvent.BaseEvent.eid",
        extra_headers={"X-AIHub-User-Token": "tok"},
    )

    sent_headers = js.publish_async.await_args.kwargs["headers"]
    assert sent_headers.get("X-AIHub-User-Token") == "tok"
    assert "Nats-Msg-Id" in sent_headers


@pytest.mark.asyncio
async def test_nc_publisher_threads_extra_headers_into_published_message():
    """Same contract on the NATS Core (ephemeral) path."""
    nc = MagicMock()
    nc.publish = AsyncMock()

    publisher = NCPublisher(name="test", nc=nc)

    await publisher.publish_event(
        BaseEvent(),
        "agent.MyAgent.profile.thread.display.run.displayEvent.BaseEvent.eid",
        extra_headers={"X-AIHub-User-Token": "tok"},
    )

    sent_headers = nc.publish.await_args.kwargs["headers"]
    assert sent_headers.get("X-AIHub-User-Token") == "tok"
