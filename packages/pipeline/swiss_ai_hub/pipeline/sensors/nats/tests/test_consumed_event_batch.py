import asyncio
from collections.abc import AsyncIterator
from itertools import count
from unittest.mock import AsyncMock, MagicMock

import pytest
from swiss_ai_hub.core.events.pipeline import SourceUpdatedEvent
from swiss_ai_hub.core.polling import PolledMessage

from swiss_ai_hub.pipeline.sensors.nats.consumed_event_batch import _MAX_DRAIN_MESSAGES, ConsumedEventBatch


def _message(sequence: int, event: object | None = None) -> MagicMock:
    """A stand-in for a polled message; ``spec`` keeps it an instance of ``PolledMessage`` so the
    Pydantic model accepts it."""
    message = MagicMock(spec=PolledMessage)
    message.event = event if event is not None else SourceUpdatedEvent(path=f"docs/{sequence}.pdf")
    message.sequence = sequence
    message.ack = AsyncMock()
    message.nak = AsyncMock()
    return message


def _poller_yielding(fetches: list[list[MagicMock]]) -> MagicMock:
    """Mock poller replaying one list of messages per ``poll()`` call, then nothing."""
    poller = MagicMock()
    remaining = list(fetches)

    async def _poll(*_args, **_kwargs) -> AsyncIterator[MagicMock]:
        current = remaining.pop(0) if remaining else []
        for message in current:
            yield message

    poller.poll = _poll
    return poller


def _poller_never_running_dry(per_fetch: int) -> MagicMock:
    """Mock poller whose fetches never come back empty, standing in for an upload still in flight."""
    poller = MagicMock()
    sequences = count(1)

    async def _poll(*_args, **_kwargs) -> AsyncIterator[MagicMock]:
        for _ in range(per_fetch):
            yield _message(next(sequences))

    poller.poll = _poll
    return poller


class TestDrain:
    @pytest.mark.asyncio
    async def test_empty_stream_yields_empty_batch(self) -> None:
        batch = await ConsumedEventBatch.drain(_poller_yielding([]))

        assert batch.count == 0
        assert batch.max_sequence == 0

    @pytest.mark.asyncio
    async def test_drains_across_fetches_until_one_comes_back_empty(self) -> None:
        """A single fetch per tick is what stretches a bulk upload over many ticks; the whole
        backlog has to drain within one tick."""
        fetches = [[_message(sequence) for sequence in range(start, start + 100)] for start in (1, 101, 201)]

        batch = await ConsumedEventBatch.drain(_poller_yielding(fetches))

        assert batch.count == 300
        assert batch.max_sequence == 300

    @pytest.mark.asyncio
    async def test_non_matching_event_type_is_naked_and_excluded(self) -> None:
        wrong = _message(1, event=MagicMock(name="UnexpectedEventType"))
        valid = _message(2)

        batch = await ConsumedEventBatch.drain(_poller_yielding([[wrong, valid]]))

        assert batch.count == 1
        assert batch.max_sequence == 2
        wrong.nak.assert_awaited_once()
        wrong.ack.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_drain_stops_at_the_cap(self) -> None:
        """Messages are held unacked until the tick decides, so the drain must finish well inside
        the consumer's ack deadline. Leftovers are collected on the next tick."""
        oversized = [[_message(seq) for seq in range(start, start + 1000)] for start in range(1, 20_000, 1000)]

        batch = await ConsumedEventBatch.drain(_poller_yielding(oversized))

        assert batch.count == _MAX_DRAIN_MESSAGES

    @pytest.mark.asyncio
    async def test_short_fetch_ends_the_drain_while_a_producer_is_still_publishing(self) -> None:
        """A bulk upload in progress keeps the stream non-empty, so stopping only on an empty fetch
        would follow the producer until the tick blew the 60 s deadline Dagster puts on a sensor
        evaluation — dropping the batch and its cursor with it."""
        batch = await asyncio.wait_for(ConsumedEventBatch.drain(_poller_never_running_dry(5)), timeout=5.0)

        assert batch.count == 5

    @pytest.mark.asyncio
    async def test_full_fetches_keep_draining_up_to_the_cap(self) -> None:
        """A full fetch means more was waiting, so a real backlog still drains in one tick."""
        batch = await asyncio.wait_for(ConsumedEventBatch.drain(_poller_never_running_dry(100)), timeout=30.0)

        assert batch.count == _MAX_DRAIN_MESSAGES

    @pytest.mark.asyncio
    async def test_messages_are_not_acked_while_draining(self) -> None:
        """Acks are deferred until the tick knows whether it will request a run."""
        messages = [_message(1), _message(2)]

        await ConsumedEventBatch.drain(_poller_yielding([messages]))

        for message in messages:
            message.ack.assert_not_awaited()


class TestAcknowledgement:
    @pytest.mark.asyncio
    async def test_ack_all_acks_every_message(self) -> None:
        messages = [_message(1), _message(2)]

        await ConsumedEventBatch(messages=messages).ack_all()

        for message in messages:
            message.ack.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_nak_all_naks_every_message(self) -> None:
        messages = [_message(1), _message(2)]

        await ConsumedEventBatch(messages=messages).nak_all()

        for message in messages:
            message.nak.assert_awaited_once()
