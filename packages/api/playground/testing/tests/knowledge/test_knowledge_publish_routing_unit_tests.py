from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from swiss_ai_hub.core.persistence.rag.datalake.entities import IngestorType

from swiss_ai_hub.api.routes.knowledge.knowledge_service import KnowledgeService

_SERVICE_MODULE = "swiss_ai_hub.api.routes.knowledge.knowledge_service"

DATABASE = "researchdocs"
CONTAINER = "researchdocs"
FILE_PATH = "reports/q3.pdf"


def _bucket(ingestor: str) -> MagicMock:
    return MagicMock(bucket_name=CONTAINER, db_name=DATABASE, ingestor=ingestor)


async def _publish(ingestor: str) -> tuple[str, str, str]:
    """Publishes one SourceUpdatedEvent and returns (stream_name, stream_subject, subject)."""
    publisher = MagicMock(ensure_stream_exists=AsyncMock(), publish_event=AsyncMock())
    with (
        patch(f"{_SERVICE_MODULE}.BucketEntity") as bucket_cls,
        patch(f"{_SERVICE_MODULE}.JSPublisher", return_value=publisher),
    ):
        bucket_cls.get_bucket_by_db_name.return_value = _bucket(ingestor)
        await KnowledgeService._publish_source_updated_event(
            nc=MagicMock(jetstream=MagicMock(return_value=MagicMock())),
            database=DATABASE,
            container=CONTAINER,
            file_path=FILE_PATH,
        )

    stream_name, stream_subject = publisher.ensure_stream_exists.await_args.args
    subject = publisher.publish_event.await_args.args[1]
    return stream_name, stream_subject, subject


class TestLegacyBucketsKeepTheirPerInstanceSubject:
    """The frozen images can never be rebuilt to read a new subject, so the API must keep speaking theirs."""

    @pytest.mark.parametrize("ingestor", [IngestorType.DEFAULT_RAG.value, IngestorType.SHARED_RAG.value])
    @pytest.mark.asyncio
    async def test_publishes_to_the_datalake_keyed_stream(self, ingestor):
        stream_name, stream_subject, subject = await _publish(ingestor)

        assert stream_name == f"pipeline_datalake_{CONTAINER}_knowledge_{DATABASE}_stream"
        assert stream_subject == f"pipeline.datalake.{CONTAINER}.to.knowledge.{DATABASE}.*.*.*"
        assert subject.startswith(f"pipeline.datalake.{CONTAINER}.to.knowledge.{DATABASE}.")


class TestSelfServiceBucketsUseTheTypeKeyedSubject:
    @pytest.mark.asyncio
    async def test_publishes_to_one_stream_per_ingestor(self):
        stream_name, stream_subject, subject = await _publish(IngestorType.DOCUMENT_INGESTION.value)

        assert stream_name == "pipeline_document_ingestion_stream"
        assert stream_subject == "pipeline.document_ingestion.>"
        assert subject.startswith(f"pipeline.document_ingestion.{CONTAINER}.to.knowledge.{DATABASE}.")

    @pytest.mark.asyncio
    async def test_a_custom_ingestor_gets_its_own_stream(self):
        stream_name, stream_subject, _ = await _publish("acme_ocr")

        assert stream_name == "pipeline_acme_ocr_stream"
        assert stream_subject == "pipeline.acme_ocr.>"


class TestTheTwoPipelineFamiliesDoNotCollide:
    @pytest.mark.asyncio
    async def test_legacy_and_self_service_streams_are_disjoint(self):
        """A shared or overlapping subject filter would make JetStream reject one of the two streams."""
        legacy_name, legacy_filter, _ = await _publish(IngestorType.DEFAULT_RAG.value)
        modern_name, modern_filter, _ = await _publish(IngestorType.DOCUMENT_INGESTION.value)

        assert legacy_name != modern_name
        # The token after "pipeline." is what separates them: "datalake" for the legacy per-instance
        # streams, the ingestor id for the type-keyed ones. IngestorEntity reserves "datalake" so a
        # custom pipeline can never claim it and land inside a legacy stream's filter.
        assert legacy_filter.split(".")[1] == "datalake"
        assert modern_filter.split(".")[1] == "document_ingestion"
        assert not modern_filter.startswith("pipeline.datalake.")
