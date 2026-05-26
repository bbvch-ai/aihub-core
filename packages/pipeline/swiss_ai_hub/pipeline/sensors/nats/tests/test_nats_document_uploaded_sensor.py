from collections.abc import AsyncIterator
from unittest.mock import AsyncMock, MagicMock

import pytest
from dagster import DefaultSensorStatus, SensorDefinition, job, op
from swiss_ai_hub.core.events.pipeline import SourceUpdatedEvent

from swiss_ai_hub.pipeline.sensors.nats.nats_document_uploaded_sensor import (
    _consume_latest_event,
    nats_document_uploaded_sensor,
)


def _poller_yielding(items: list[tuple]) -> MagicMock:
    """Build a mock `JSPoller` whose ``poll(...)`` yields the given ``(event, ack, nak)`` tuples."""
    poller = MagicMock()

    async def _poll(*_args, **_kwargs) -> AsyncIterator[tuple]:
        for item in items:
            yield item

    poller.poll = _poll
    return poller


class TestConsumeLatestEvent:
    """Unit tests for the polling loop extracted out of ``check_for_events``."""

    @pytest.mark.asyncio
    async def test_empty_stream_returns_none(self) -> None:
        poller = _poller_yielding([])

        result = await _consume_latest_event(poller)

        assert result is None

    @pytest.mark.asyncio
    async def test_single_event_returns_event_and_acks(self) -> None:
        event = SourceUpdatedEvent(path="docs/a.pdf")
        ack, nak = AsyncMock(), AsyncMock()
        poller = _poller_yielding([(event, ack, nak)])

        result = await _consume_latest_event(poller)

        assert result is event
        ack.assert_awaited_once()
        nak.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_multiple_events_returns_last_and_acks_all(self) -> None:
        """When several valid events arrive, the helper returns the LAST one but acks them all."""
        event_a = SourceUpdatedEvent(path="docs/a.pdf")
        event_b = SourceUpdatedEvent(path="docs/b.pdf")
        event_c = SourceUpdatedEvent(path="docs/c.pdf")
        acks = [AsyncMock(), AsyncMock(), AsyncMock()]
        naks = [AsyncMock(), AsyncMock(), AsyncMock()]
        poller = _poller_yielding(list(zip([event_a, event_b, event_c], acks, naks, strict=True)))

        result = await _consume_latest_event(poller)

        assert result is event_c
        for ack in acks:
            ack.assert_awaited_once()
        for nak in naks:
            nak.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_non_matching_event_type_is_naked_and_skipped(self) -> None:
        """An event that is NOT a ``SourceUpdatedEvent`` must be nak'd (no ack) and excluded from ``latest_event``."""
        wrong_event = MagicMock(name="UnexpectedEventType")
        ack, nak = AsyncMock(), AsyncMock()
        poller = _poller_yielding([(wrong_event, ack, nak)])

        result = await _consume_latest_event(poller)

        assert result is None
        ack.assert_not_awaited()
        nak.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_mixed_events_returns_last_valid(self) -> None:
        """An invalid event between two valid ones is nak'd; the last VALID event wins."""
        valid_a = SourceUpdatedEvent(path="docs/a.pdf")
        invalid = MagicMock(name="UnexpectedEventType")
        valid_b = SourceUpdatedEvent(path="docs/b.pdf")
        ack_a, ack_invalid, ack_b = AsyncMock(), AsyncMock(), AsyncMock()
        nak_a, nak_invalid, nak_b = AsyncMock(), AsyncMock(), AsyncMock()
        poller = _poller_yielding(
            [
                (valid_a, ack_a, nak_a),
                (invalid, ack_invalid, nak_invalid),
                (valid_b, ack_b, nak_b),
            ]
        )

        result = await _consume_latest_event(poller)

        assert result is valid_b
        ack_a.assert_awaited_once()
        ack_b.assert_awaited_once()
        ack_invalid.assert_not_awaited()
        nak_invalid.assert_awaited_once()
        nak_a.assert_not_awaited()
        nak_b.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_ack_failure_naks_and_continues(self) -> None:
        """If ``ack()`` raises, the helper logs, nak()s, and keeps processing later events."""
        event_a = SourceUpdatedEvent(path="docs/a.pdf")
        event_b = SourceUpdatedEvent(path="docs/b.pdf")
        ack_a = AsyncMock(side_effect=RuntimeError("ack failure"))
        ack_b = AsyncMock()
        nak_a, nak_b = AsyncMock(), AsyncMock()
        poller = _poller_yielding([(event_a, ack_a, nak_a), (event_b, ack_b, nak_b)])

        result = await _consume_latest_event(poller)

        # event_b was the last successfully-handled event.
        assert result is event_b
        ack_a.assert_awaited_once()
        nak_a.assert_awaited_once()  # nak'd after ack_a failed
        ack_b.assert_awaited_once()
        nak_b.assert_not_awaited()


class TestNatsDocumentUploadedSensorFactory:
    """Smoke tests for the public factory — verifies the returned Dagster sensor has correct metadata."""

    def test_returns_sensor_with_expected_metadata(self) -> None:
        @op
        def _noop() -> None: ...

        @job
        def my_pipeline_job() -> None:
            _noop()

        topic_manager = MagicMock()

        sensor = nats_document_uploaded_sensor(my_pipeline_job, topic_manager)

        assert isinstance(sensor, SensorDefinition)
        assert sensor.name == "NATSDocumentUploadedSensorFor_my_pipeline_job"
        assert sensor.default_status is DefaultSensorStatus.RUNNING
        assert sensor.minimum_interval_seconds == 60
