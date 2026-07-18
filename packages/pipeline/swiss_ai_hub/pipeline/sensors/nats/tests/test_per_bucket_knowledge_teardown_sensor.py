from collections.abc import AsyncIterator
from unittest.mock import AsyncMock, MagicMock

import pytest
from swiss_ai_hub.core.events.pipeline import KnowledgeTeardownRequestedEvent

from swiss_ai_hub.pipeline.sensors.nats.per_bucket_knowledge_teardown_sensor import (
    _consume_teardown_events,
    _run_request_for,
)
from swiss_ai_hub.pipeline.util.run_routing import BUCKET_RUN_TAG

REGISTRY = "rag_document_partitions"


def _poller_yielding(items: list[tuple]) -> MagicMock:
    poller = MagicMock()

    async def _poll(*_args, **_kwargs) -> AsyncIterator[tuple]:
        for item in items:
            yield item

    poller.poll = _poll
    return poller


class TestConsumeTeardownEvents:
    @pytest.mark.asyncio
    async def test_empty_stream_returns_no_events(self) -> None:
        assert await _consume_teardown_events(_poller_yielding([])) == []

    @pytest.mark.asyncio
    async def test_returns_every_valid_event_and_acks_each(self) -> None:
        event_a = KnowledgeTeardownRequestedEvent.for_database(bucket_id="b1", bucket_name="a", db_name="a")
        event_b = KnowledgeTeardownRequestedEvent.for_namespace(
            bucket_id="b1", bucket_name="a", db_name="a", namespace_id="n1", namespace_name="ns", folder_name="ns"
        )
        ack_a, ack_b = AsyncMock(), AsyncMock()
        nak_a, nak_b = AsyncMock(), AsyncMock()
        poller = _poller_yielding([(event_a, ack_a, nak_a), (event_b, ack_b, nak_b)])

        result = await _consume_teardown_events(poller)

        assert result == [event_a, event_b]
        ack_a.assert_awaited_once()
        ack_b.assert_awaited_once()
        nak_a.assert_not_awaited()
        nak_b.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_non_matching_event_type_is_naked_and_skipped(self) -> None:
        ack, nak = AsyncMock(), AsyncMock()
        poller = _poller_yielding([(MagicMock(name="UnexpectedEvent"), ack, nak)])

        result = await _consume_teardown_events(poller)

        assert result == []
        ack.assert_not_awaited()
        nak.assert_awaited_once()


class TestRunRequestFor:
    def test_database_event_produces_a_deduped_bucket_tagged_run_request(self) -> None:
        event = KnowledgeTeardownRequestedEvent.for_database(
            bucket_id="b1", bucket_name="researchdocs", db_name="researchdocs"
        )

        run_request = _run_request_for(event, REGISTRY)

        assert run_request.run_key == event.event_id
        assert run_request.tags[BUCKET_RUN_TAG] == "researchdocs"
        config = run_request.run_config["ops"]["knowledge_teardown_op"]["config"]
        assert config["teardown_type"] == "database"
        assert config["db_name"] == "researchdocs"
        assert config["partition_registry_name"] == REGISTRY
        assert config.get("namespace_id") is None

    def test_namespace_event_carries_the_namespace_fields(self) -> None:
        event = KnowledgeTeardownRequestedEvent.for_namespace(
            bucket_id="b1",
            bucket_name="researchdocs",
            db_name="researchdocs",
            namespace_id="ns1",
            namespace_name="reports",
            folder_name="reports",
        )

        run_request = _run_request_for(event, REGISTRY)

        config = run_request.run_config["ops"]["knowledge_teardown_op"]["config"]
        assert config["teardown_type"] == "namespace"
        assert config["namespace_id"] == "ns1"
        assert config["namespace_name"] == "reports"
        assert config["folder_name"] == "reports"
