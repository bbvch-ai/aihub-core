import asyncio
import logging
import time
from typing import Annotated

from dagster import DefaultSensorStatus, RunRequest, SensorEvaluationContext, SkipReason, sensor
from dagster._core.definitions.target import ExecutableDefinition
from swiss_ai_hub.core.infrastructure import NatsSettings
from swiss_ai_hub.core.polling import JSPoller
from swiss_ai_hub.core.topic_managers import PipelineInstanceTopicManager

from swiss_ai_hub.pipeline.sensors.nats.consumed_event_batch import ConsumedEventBatch
from swiss_ai_hub.pipeline.sensors.nats.observation_run_decider import ObservationRunDecider
from swiss_ai_hub.pipeline.sensors.nats.observation_run_history import ObservationRunHistory
from swiss_ai_hub.pipeline.sensors.nats.observation_sensor_cursor import ObservationSensorCursor
from swiss_ai_hub.pipeline.sensors.single_flight_run_guard import SingleFlightRunGuard

logger = logging.getLogger(__name__)


def nats_document_uploaded_sensor(
    job: ExecutableDefinition,
    topic_manager: Annotated[PipelineInstanceTopicManager, "Topic manager for the pipeline instance"],
):
    """
    Creates a Dagster sensor that polls NATS JetStream for SourceUpdatedEvent messages.

    An observation scans the entire bucket, so a burst of uploads needs one run, not one per tick.
    The sensor keeps at most one observation queued or running and re-arms itself through its
    cursor whenever events arrive while a run is already in flight.
    """

    @sensor(
        job=job,
        minimum_interval_seconds=60,
        default_status=DefaultSensorStatus.RUNNING,
        name=f"NATSDocumentUploadedSensorFor_{job.name}",
        description="Polls NATS JetStream for SourceUpdatedEvent messages and keeps one pipeline run in flight.",
    )
    def _nats_document_uploaded_sensor(context: SensorEvaluationContext):
        """Poll NATS JetStream for SourceUpdatedEvent messages and trigger a single pipeline run."""

        def decide(cursor: ObservationSensorCursor, batch: ConsumedEventBatch) -> RunRequest | SkipReason:
            """Fold the drained batch into the cursor and decide what this tick should do."""
            now = time.time()

            if batch.count:
                cursor.pending_events += batch.count
                if cursor.first_pending_at is None:
                    cursor.first_pending_at = now
                cursor.max_sequence = max(cursor.max_sequence, batch.max_sequence)

            in_flight = SingleFlightRunGuard.in_flight_run(context.instance, job.name)
            if in_flight:
                # A running observation cannot be trusted to have seen files that landed after it
                # took its own snapshot of the bucket, so owe exactly one follow-up instead.
                cursor.followup_armed = cursor.followup_armed or bool(batch.count)
                return SkipReason(
                    f"Observation run {in_flight.run_id} is already in flight ({in_flight.status.value})."
                )

            truncation_run_id = ObservationRunHistory.latest_truncating_run_id(context.instance, job.name)
            requested_run_missing = bool(cursor.requested_run_key) and not ObservationRunHistory.run_exists_for_run_key(
                context.instance, job.name, cursor.requested_run_key
            )
            reason = ObservationRunDecider.reason_to_request(
                cursor=cursor,
                now=now,
                truncation_run_id=truncation_run_id,
                requested_run_missing=requested_run_missing,
            )
            if not reason:
                return SkipReason(f"Debouncing {cursor.pending_events} pending event(s).")

            # Guard on the key itself, not on an empty batch: a batch whose sequences were all seen
            # before leaves max_sequence unchanged too, which happens when the stream is recreated
            # or restored and its sequence numbering restarts. Reusing the key we last requested
            # would let Dagster's idempotence check drop the very run being re-armed.
            pipeline_id = f"{topic_manager.source_id}_to_{topic_manager.target_id}"
            run_key = f"{pipeline_id}_seq_{cursor.max_sequence}_r{cursor.rearm_count}"
            if run_key == cursor.requested_run_key:
                cursor.rearm_count += 1
                run_key = f"{pipeline_id}_seq_{cursor.max_sequence}_r{cursor.rearm_count}"

            cursor.pending_events = 0
            cursor.first_pending_at = None
            cursor.followup_armed = False
            cursor.handled_truncation = truncation_run_id or cursor.handled_truncation
            cursor.requested_run_key = run_key

            logger.info(f"Requesting observation run {run_key}: {reason}")
            return RunRequest(run_key=run_key)

        async def evaluate() -> tuple[str, RunRequest | SkipReason]:
            """Drain, decide and acknowledge on one connection.

            Acking only once the outcome is settled means a tick that fails partway leaves the
            events unacknowledged for JetStream to redeliver, rather than dropping the trigger.
            """
            nc = None
            batch = ConsumedEventBatch()
            try:
                nc = await NatsSettings.create_client()
                js = nc.jetstream()

                stream_name, stream_subject = topic_manager.get_stream()
                consumer_name = (
                    f"dagster_sensor_{topic_manager.source_type}_{topic_manager.source_id}"
                    f"_to_{topic_manager.target_type}_{topic_manager.target_id}"
                )

                poller = JSPoller(js, stream_name, stream_subject, consumer_name)
                await poller.ensure_stream_exists()
                await poller.ensure_consumer_exists()

                batch = await ConsumedEventBatch.drain(poller)

                cursor = ObservationSensorCursor.from_cursor(context.cursor)
                result = decide(cursor, batch)

                await batch.ack_all()
                return cursor.model_dump_json(), result
            except Exception:
                await batch.nak_all()
                raise
            finally:
                if nc:
                    await nc.close()

        updated_cursor, result = asyncio.run(evaluate())
        context.update_cursor(updated_cursor)
        yield result

    return _nats_document_uploaded_sensor
