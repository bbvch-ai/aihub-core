import asyncio
import logging
from typing import Annotated

from dagster import DefaultSensorStatus, RunRequest, SensorEvaluationContext, sensor
from dagster._core.definitions.target import ExecutableDefinition
from swiss_ai_hub.core.events.pipeline import SourceUpdatedEvent
from swiss_ai_hub.core.infrastructure import NatsSettings
from swiss_ai_hub.core.polling import JSPoller
from swiss_ai_hub.core.topic_managers import PipelineInstanceTopicManager

logger = logging.getLogger(__name__)


async def _consume_latest_event(poller: JSPoller) -> SourceUpdatedEvent | None:
    """Drain the JetStream poller, acking valid `SourceUpdatedEvent`s.

    Returns the most recent valid event (or None if none were found). Non-matching
    event types and ack failures are negatively-acknowledged so JetStream redelivers.
    """
    latest_event: SourceUpdatedEvent | None = None
    async for event, ack, nak in poller.poll(batch_size=10, timeout=1.0):
        if not isinstance(event, SourceUpdatedEvent):
            logger.warning(f"Unexpected event type: {type(event)}")
            await nak()
            continue
        try:
            latest_event = event
            await ack()
        except Exception as e:
            logger.exception(f"Failed to process event: {e}")
            await nak()
    return latest_event


def nats_document_uploaded_sensor(
    job: ExecutableDefinition,
    topic_manager: Annotated[PipelineInstanceTopicManager, "Topic manager for the pipeline instance"],
):
    """
    Creates a Dagster sensor that polls NATS JetStream for SourceUpdatedEvent messages.

    When documents are uploaded and validated, SourceUpdatedEvents are published to NATS.
    This sensor polls for these events and triggers a single pipeline run to process all documents.
    """

    @sensor(
        job=job,
        minimum_interval_seconds=60,
        default_status=DefaultSensorStatus.RUNNING,
        name=f"NATSDocumentUploadedSensorFor_{job.name}",
        description="Polls NATS JetStream for SourceUpdatedEvent messages and triggers a single pipeline run.",
    )
    def _nats_document_uploaded_sensor(context: SensorEvaluationContext):
        """Poll NATS JetStream for SourceUpdatedEvent messages and trigger a single pipeline run."""

        async def check_for_events():
            nc = None
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

                latest_event = await _consume_latest_event(poller)
                if not latest_event:
                    return []

                run_key = (
                    f"{topic_manager.source_id}_to_{topic_manager.target_id}_{context.last_tick_completion_time or 0}"
                )
                # As an observation request will find ALL uploaded/modified documents, we only need to request 1 run
                return [RunRequest(run_key=run_key)]

            except Exception as e:
                logger.exception(f"Error in NATS sensor: {e}")
                return []

            finally:
                if nc:
                    await nc.close()

        run_requests = asyncio.run(check_for_events())
        yield from run_requests

    return _nats_document_uploaded_sensor
