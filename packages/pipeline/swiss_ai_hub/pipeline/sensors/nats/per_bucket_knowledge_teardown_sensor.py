import asyncio
import logging

from dagster import DefaultSensorStatus, RunConfig, RunRequest, SensorEvaluationContext, sensor
from dagster._core.definitions.target import ExecutableDefinition
from swiss_ai_hub.core.events.pipeline import KnowledgeTeardownRequestedEvent
from swiss_ai_hub.core.infrastructure import NatsSettings
from swiss_ai_hub.core.persistence import BucketEntity
from swiss_ai_hub.core.polling import JSPoller
from swiss_ai_hub.core.topic_managers import PipelineInstanceTopicManager

from swiss_ai_hub.pipeline.const.pipeline_names import INTERNAL_DATALAKE, INTERNAL_KNOWLEDGE_TEARDOWN
from swiss_ai_hub.pipeline.ops.teardown.knowledge_teardown_op import KnowledgeTeardownConfig
from swiss_ai_hub.pipeline.util.bucket_utils import ensure_main_db_connection
from swiss_ai_hub.pipeline.util.run_routing import BUCKET_RUN_TAG

logger = logging.getLogger(__name__)


async def _consume_teardown_events(poller: JSPoller) -> list[KnowledgeTeardownRequestedEvent]:
    """Drain the poller, acking each valid teardown event and returning them all.

    Unlike the upload sensor (latest-event-wins), every teardown event is a distinct destructive request,
    so all are returned. Non-matching event types are negatively-acknowledged so JetStream redelivers —
    though the dedicated teardown stream should only ever carry ``KnowledgeTeardownRequestedEvent``.
    """
    events: list[KnowledgeTeardownRequestedEvent] = []
    async for event, ack, nak in poller.poll(batch_size=10, timeout=1.0):
        if not isinstance(event, KnowledgeTeardownRequestedEvent):
            logger.warning(f"Unexpected event type on teardown stream: {type(event)}")
            await nak()
            continue
        try:
            events.append(event)
            await ack()
        except Exception as e:
            logger.exception(f"Failed to process teardown event: {e}")
            await nak()
    return events


def per_bucket_knowledge_teardown_sensor(job: ExecutableDefinition, *, ingestor: str):
    """NATS sensor that runs the teardown job for any owned knowledge database with a pending teardown.

    Sibling of ``per_bucket_nats_document_uploaded_sensor``, but polls each database's dedicated *teardown*
    stream. Crucially it does **not** exclude ``deleting`` buckets: a database teardown flags its bucket
    ``deleting`` (which stops ingestion), yet that row must still be enumerated here so the sensor can route
    the run — the teardown job hard-deletes the row only as its final step.
    """
    partition_registry_name = f"{ingestor}_document_partitions"

    @sensor(
        job=job,
        minimum_interval_seconds=30,
        default_status=DefaultSensorStatus.RUNNING,
        name="PerBucketKnowledgeTeardownSensor",
        description="Polls each owned knowledge database's teardown JetStream for KnowledgeTeardownRequestedEvents.",
    )
    def _sensor(context: SensorEvaluationContext):
        async def check_for_events() -> list[RunRequest]:
            nc = None
            run_requests: list[RunRequest] = []
            try:
                ensure_main_db_connection()
                owned_buckets = [b for b in BucketEntity.get_all_buckets() if b.ingestor == ingestor]
                if not owned_buckets:
                    return []

                nc = await NatsSettings.create_client()
                js = nc.jetstream()

                for bucket in owned_buckets:
                    topic_manager = PipelineInstanceTopicManager(
                        source_type=INTERNAL_DATALAKE,
                        source_id=bucket.bucket_name,
                        target_type=INTERNAL_KNOWLEDGE_TEARDOWN,
                        target_id=bucket.db_name,
                    )
                    stream_name, stream_subject = topic_manager.get_stream()
                    poller = JSPoller(js, stream_name, stream_subject, f"dagster_teardown_sensor_{bucket.bucket_name}")
                    await poller.ensure_stream_exists()
                    await poller.ensure_consumer_exists()

                    for event in await _consume_teardown_events(poller):
                        run_requests.append(_run_request_for(event, partition_registry_name))

                return run_requests

            except Exception as e:
                context.log.exception(f"Error in per-bucket teardown sensor, skipping this tick: {e}")
                return []

            finally:
                if nc:
                    await nc.close()

        yield from asyncio.run(check_for_events())

    return _sensor


def _run_request_for(event: KnowledgeTeardownRequestedEvent, partition_registry_name: str) -> RunRequest:
    """Build a deduplicated (by event id) teardown run request from a teardown event."""
    return RunRequest(
        run_key=event.event_id,
        run_config=RunConfig(
            ops={
                "knowledge_teardown_op": KnowledgeTeardownConfig(
                    teardown_type=event.teardown_type,
                    bucket_id=event.bucket_id,
                    bucket_name=event.bucket_name,
                    db_name=event.db_name,
                    partition_registry_name=partition_registry_name,
                    namespace_id=event.namespace_id,
                    namespace_name=event.namespace_name,
                    folder_name=event.folder_name,
                )
            }
        ),
        tags={BUCKET_RUN_TAG: event.bucket_name},
    )
