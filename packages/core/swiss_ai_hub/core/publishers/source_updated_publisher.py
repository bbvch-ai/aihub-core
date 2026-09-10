import logging
from typing import Annotated

from nats.aio.client import Client as NATS

from swiss_ai_hub.core.events.pipeline.source_updated_event import SourceUpdatedEvent
from swiss_ai_hub.core.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn
from swiss_ai_hub.core.persistence.rag.datalake.entities.bucket_entity import BucketEntity
from swiss_ai_hub.core.persistence.rag.datalake.entities.ingestor_type import IngestorType
from swiss_ai_hub.core.publishers.js_publisher import JSPublisher
from swiss_ai_hub.core.topic_managers.pipeline.pipeline_instance_topic_manager import PipelineInstanceTopicManager
from swiss_ai_hub.core.topic_managers.pipeline.pipeline_subject_types import PipelineSourceType, PipelineTargetType
from swiss_ai_hub.core.topic_managers.pipeline.pipeline_type_topic_manager import PipelineTypeTopicManager

logger = logging.getLogger(__name__)

_LEGACY_INGESTORS = {IngestorType.DEFAULT_RAG.value, IngestorType.SHARED_RAG.value}


class SourceUpdatedPublisher:
    """
    Tells the ingestion pipeline that owns a knowledge database that a file in its data lake was added or removed.

    Shared by everything that writes into a data lake — the API after a browser upload or delete, and source
    pipelines after a sync — so the ingestion pipeline sees one contract however the file got there. The subject
    is keyed on the owning ingestor rather than on the bucket, so a pipeline needs one JetStream stream and one
    consumer however many databases it serves. Frozen legacy pipelines keep the old per-instance subject: their
    images can no longer be changed to read a new one. The stream is ensured first, because a file that lands
    before the sensor's first tick created the stream would otherwise be dropped until the next scheduled observation.
    """

    @staticmethod
    @trace_fn
    async def publish(
        nc: Annotated[NATS, "Connected NATS client"],
        bucket: Annotated[BucketEntity, "Knowledge database whose data lake changed"],
        file_path: Annotated[str, "Object key of the added or removed file, relative to the bucket"],
    ) -> None:
        if bucket.ingestor in _LEGACY_INGESTORS:
            topic_manager = PipelineInstanceTopicManager(
                source_type=PipelineSourceType.DATALAKE,
                source_id=bucket.bucket_name,
                target_type=PipelineTargetType.KNOWLEDGE,
                target_id=bucket.db_name,
            )
            stream_name, stream_subject = topic_manager.get_stream()
            subject_for = topic_manager.get_subject_for_specific_event_in_pipeline_instance
        else:
            type_topic_manager = PipelineTypeTopicManager(pipeline_type=bucket.ingestor)
            stream_name, stream_subject = type_topic_manager.get_stream()

            def subject_for(run_key: str, event_name: str, event_id: str) -> str:
                return type_topic_manager.get_subject_for_source_updated(
                    bucket_name=bucket.bucket_name,
                    db_name=bucket.db_name,
                    run_key=run_key,
                    event_name=event_name,
                    event_id=event_id,
                )

        event = SourceUpdatedEvent(path=file_path)
        subject = subject_for(run_key=event.event_id, event_name=event.event_name, event_id=event.event_id)

        publisher = JSPublisher(name="SourceUpdatedPublisher", js=nc.jetstream())
        await publisher.ensure_stream_exists(stream_name, stream_subject)
        await publisher.publish_event(event, subject)

        logger.info(f"Published SourceUpdatedEvent for file {file_path} to subject {subject}")
