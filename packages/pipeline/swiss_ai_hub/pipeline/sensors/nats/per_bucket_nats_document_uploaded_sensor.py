import asyncio
import logging
import time
from typing import Annotated

from dagster import DefaultSensorStatus, RunRequest, SensorEvaluationContext, SkipReason, sensor
from dagster._core.definitions.target import ExecutableDefinition
from swiss_ai_hub.core.infrastructure import NatsSettings
from swiss_ai_hub.core.persistence import BucketEntity
from swiss_ai_hub.core.polling import JSPoller
from swiss_ai_hub.core.topic_managers import PipelineTypeTopicManager

from swiss_ai_hub.pipeline.sensors.nats.consumed_event_batch import ConsumedEventBatch
from swiss_ai_hub.pipeline.sensors.nats.observation_run_decider import ObservationRunDecider
from swiss_ai_hub.pipeline.sensors.nats.observation_run_history import ObservationRunHistory
from swiss_ai_hub.pipeline.sensors.nats.observation_sensor_cursor import ObservationSensorCursor
from swiss_ai_hub.pipeline.sensors.nats.routed_observation_sensor_cursor import RoutedObservationSensorCursor
from swiss_ai_hub.pipeline.sensors.single_flight_run_guard import SingleFlightRunGuard
from swiss_ai_hub.pipeline.util.bucket_utils import ensure_main_db_connection
from swiss_ai_hub.pipeline.util.run_routing import BUCKET_RUN_TAG

logger = logging.getLogger(__name__)


def per_bucket_nats_document_uploaded_sensor(
    job: ExecutableDefinition,
    *,
    ingestor: Annotated[str, "Ingestor whose databases this pipeline serves"],
):
    """Triggers a bucket-tagged observe run for any knowledge database this pipeline owns that has uploads.

    Uploads for every database arrive on one ingestor-keyed stream, so the sensor holds a single stream
    and a single durable consumer no matter how many databases exist. Each tick drains that stream once,
    groups the batch by bucket, and then runs the same debounce/single-flight decision per database that
    a one-database pipeline runs for itself.

    Cluster safety comes from Dagster, not from NATS: sensors evaluate only on the daemon, which is a
    singleton, and each request carries a run key that Dagster deduplicates. Running more than one
    Dagster daemon is unsupported. Duplicate triggers would in any case be harmless — an observation is
    a full reconciliation of the bucket, so an extra run converges to the same state.
    """
    topic_manager = PipelineTypeTopicManager(pipeline_type=ingestor)

    @sensor(
        job=job,
        minimum_interval_seconds=60,
        default_status=DefaultSensorStatus.RUNNING,
        name=f"NATSDocumentUploadedSensorFor_{job.name}",
        description="Polls this pipeline's JetStream for SourceUpdatedEvents and keeps one run per database in flight.",
    )
    def _sensor(context: SensorEvaluationContext):
        def decide(
            bucket_name: str, cursor: ObservationSensorCursor, batch: ConsumedEventBatch
        ) -> RunRequest | SkipReason:
            """Fold this bucket's share of the drained batch into its cursor and decide what to do."""
            now = time.time()
            cursor.absorb(batch, now)
            bucket_tag = {BUCKET_RUN_TAG: bucket_name}

            in_flight = SingleFlightRunGuard.in_flight_run(context.instance, job.name, bucket_tag)
            if in_flight:
                cursor.arm_followup(batch)
                return SkipReason(
                    f"{bucket_name}: observation run {in_flight.run_id} is already in flight "
                    f"({in_flight.status.value})."
                )

            truncation_run_id = ObservationRunHistory.latest_truncating_run_id(
                context.instance, job.name, bucket_tag
            )
            reason = ObservationRunDecider.reason_to_request(
                cursor=cursor,
                now=now,
                truncation_run_id=truncation_run_id,
                requested_run_missing=ObservationRunHistory.requested_run_missing(
                    context.instance, job.name, cursor.requested_run_key
                ),
            )
            if not reason:
                return SkipReason(f"{bucket_name}: debouncing {cursor.pending_events} pending event(s).")

            run_key = cursor.next_run_key(f"{ingestor}_{bucket_name}")
            cursor.mark_requested(run_key, truncation_run_id)

            logger.info(f"Requesting observation run {run_key} for {bucket_name}: {reason}")
            return RunRequest(run_key=run_key, tags=bucket_tag)

        async def evaluate() -> tuple[str, list[RunRequest | SkipReason]]:
            """Drain, decide and acknowledge on one connection.

            Acking only once every bucket's outcome is settled means a tick that fails partway leaves
            the events unacknowledged for JetStream to redeliver, rather than dropping the trigger.
            """
            nc = None
            batches: dict[str, ConsumedEventBatch] = {}
            try:
                ensure_main_db_connection()
                # A ``deleting`` database must stop being ingested at once; its events are acked and
                # dropped below so JetStream does not redeliver them until teardown removes the row.
                owned = {
                    bucket.bucket_name: bucket
                    for bucket in BucketEntity.get_all_buckets()
                    if bucket.ingestor == ingestor and not bucket.deleting
                }

                # One connection per tick, not cached between ticks: each tick runs in its own
                # asyncio.run() event loop, and a nats client is bound to the loop it was created on.
                nc = await NatsSettings.create_client()
                stream_name, stream_subject = topic_manager.get_stream()
                poller = JSPoller(nc.jetstream(), stream_name, stream_subject, f"dagster_{ingestor}_sensor")
                await poller.ensure_stream_exists()
                await poller.ensure_consumer_exists()

                batches = await ConsumedEventBatch.drain_grouped(poller, PipelineTypeTopicManager.bucket_from_subject)

                unowned = set(batches) - set(owned)
                if unowned:
                    logger.warning(f"Dropping uploads for databases this pipeline no longer serves: {sorted(unowned)}")

                cursor = RoutedObservationSensorCursor.from_cursor(context.cursor)
                results: list[RunRequest | SkipReason] = [
                    decide(bucket_name, cursor.for_bucket(bucket_name), batches.get(bucket_name, ConsumedEventBatch()))
                    for bucket_name in sorted(owned)
                ]
                cursor.prune(set(owned))

                for batch in batches.values():
                    await batch.ack_all()
                return cursor.model_dump_json(), results
            except Exception:
                for batch in batches.values():
                    await batch.nak_all()
                raise
            finally:
                if nc:
                    await nc.close()

        updated_cursor, results = asyncio.run(evaluate())
        context.update_cursor(updated_cursor)

        run_requests = [result for result in results if isinstance(result, RunRequest)]
        if run_requests:
            yield from run_requests
            return
        yield SkipReason("; ".join(str(result.skip_message) for result in results) or "No databases owned.")

    return _sensor
