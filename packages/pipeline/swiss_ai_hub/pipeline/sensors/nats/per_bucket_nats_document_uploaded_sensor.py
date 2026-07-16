import asyncio
import time

from dagster import DefaultSensorStatus, RunRequest, SensorEvaluationContext, sensor
from dagster._core.definitions.target import ExecutableDefinition
from swiss_ai_hub.core.infrastructure import NatsSettings
from swiss_ai_hub.core.persistence import BucketEntity
from swiss_ai_hub.core.polling import JSPoller
from swiss_ai_hub.core.topic_managers import PipelineInstanceTopicManager

from swiss_ai_hub.pipeline.const.pipeline_names import INTERNAL_DATALAKE, INTERNAL_KNOWLEDGE_DB
from swiss_ai_hub.pipeline.sensors.nats.nats_document_uploaded_sensor import _consume_latest_event
from swiss_ai_hub.pipeline.util.bucket_utils import ensure_main_db_connection
from swiss_ai_hub.pipeline.util.run_routing import BUCKET_RUN_TAG


def per_bucket_nats_document_uploaded_sensor(
    job: ExecutableDefinition,
    *,
    ingestor: str,
):
    """NATS sensor that triggers a bucket-tagged observe run for any owned knowledge database with uploads.

    Rather than a single wildcard JetStream stream (which would overlap the legacy per-instance streams'
    subjects — JetStream forbids that), this enumerates the databases owned by this pipeline (``ingestor``)
    and polls each one's own per-instance stream. The ingestor filter is the routing guard: legacy
    ``default``/``shared`` buckets are never polled, so they are never double-ingested.
    """

    @sensor(
        job=job,
        minimum_interval_seconds=60,
        default_status=DefaultSensorStatus.RUNNING,
        name="PerBucketNATSDocumentUploadedSensor",
        description="Polls the JetStream of each knowledge database this pipeline owns for SourceUpdatedEvents.",
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

                # One connection per tick, shared across all owned buckets. It is not cached between
                # ticks: each tick runs in its own asyncio.run() event loop, and a nats client is bound
                # to the loop it was created on, so a cached client would reference a closed loop.
                nc = await NatsSettings.create_client()
                js = nc.jetstream()
                # Unix-seconds int, stable in shape across the first (None) and later ticks, so run_keys
                # are consistent. Ticks are >=60s apart, so truncating to seconds cannot collide.
                tick = int(context.last_tick_completion_time or time.time())

                for bucket in owned_buckets:
                    topic_manager = PipelineInstanceTopicManager(
                        source_type=INTERNAL_DATALAKE,
                        source_id=bucket.bucket_name,
                        target_type=INTERNAL_KNOWLEDGE_DB,
                        target_id=bucket.db_name,
                    )
                    stream_name, stream_subject = topic_manager.get_stream()
                    poller = JSPoller(
                        js, stream_name, stream_subject, f"dagster_per_bucket_sensor_{bucket.bucket_name}"
                    )
                    await poller.ensure_stream_exists()
                    await poller.ensure_consumer_exists()

                    if await _consume_latest_event(poller):
                        run_requests.append(
                            RunRequest(
                                run_key=f"{bucket.bucket_name}_{tick}",
                                tags={BUCKET_RUN_TAG: bucket.bucket_name},
                            )
                        )
                return run_requests

            except Exception as e:
                # Surface on the Dagster sensor tick (context.log feeds the UI), not only the process
                # log, so a JetStream/DB outage is visible to operators instead of looking like an idle
                # "no work" tick.
                context.log.exception(f"Error in per-bucket NATS sensor, skipping this tick: {e}")
                return []

            finally:
                if nc:
                    await nc.close()

        yield from asyncio.run(check_for_events())

    return _sensor
