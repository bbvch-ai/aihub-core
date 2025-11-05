import asyncio
import logging
from typing import Annotated

from aihub_lib.infrastructure.nats.NatsSettings import NatsSettings
from aihub_lib.nats.events.pipeline.SourceUpdatedEvent import SourceUpdatedEvent
from aihub_lib.nats.polling.JSPoller import JSPoller
from aihub_lib.nats.topic_managers.pipeline.PipelineInstanceTopicManager import PipelineInstanceTopicManager
from dagster import DefaultSensorStatus, RunRequest, SensorEvaluationContext, sensor
from dagster._core.definitions.target import ExecutableDefinition
from nats.aio.client import Client as NATS

logger = logging.getLogger(__name__)


def nats_document_uploaded_sensor(
    job: ExecutableDefinition,
    topic_manager: Annotated[PipelineInstanceTopicManager, "Topic manager for the pipeline instance"],
):
    """
    Creates a Dagster sensor that polls NATS JetStream for SourceUpdatedEvent messages.

    When documents are uploaded and validated, SourceUpdatedEvents are published to NATS.
    This sensor polls for these events and triggers pipeline runs to process the documents.
    """

    @sensor(
        job=job,
        minimum_interval_seconds=5,
        default_status=DefaultSensorStatus.RUNNING,
    )
    def _nats_document_uploaded_sensor(context: SensorEvaluationContext):
        """Poll NATS JetStream for SourceUpdatedEvent messages and trigger pipeline runs."""

        async def check_for_events():
            nc = None
            try:
                nats_settings = NatsSettings()
                nc = await NATS().connect(nats_settings.CONNECTION_STRING)
                js = nc.jetstream()

                stream_name, stream_subject = topic_manager.get_stream()
                consumer_name = (
                    f"dagster_sensor_{topic_manager.source_type}_{topic_manager.source_id}"
                    f"_to_{topic_manager.target_type}_{topic_manager.target_id}"
                )

                poller = JSPoller(js, stream_name, stream_subject, consumer_name)
                await poller.ensure_stream_exists()
                await poller.ensure_consumer_exists()

                run_requests = []
                async for event, ack, nak in poller.poll(batch_size=10, timeout=1.0):
                    if not isinstance(event, SourceUpdatedEvent):
                        logger.warning(f"Unexpected event type: {type(event)}")
                        await nak()
                        continue

                    try:
                        logger.info(f"Processing SourceUpdatedEvent for {event.path}")
                        run_key = event.path.replace("/", "_").replace(".", "_")
                        run_requests.append(
                            RunRequest(
                                run_key=run_key,
                                run_config={
                                    "ops": {
                                        "file_path": event.path,
                                        "filename": event.filename,
                                        "content_type": event.content_type,
                                        "content_length": event.content_length,
                                    }
                                },
                            )
                        )
                        await ack()
                    except Exception as e:
                        logger.exception(f"Failed to process event: {e}")
                        await nak()

                return run_requests

            except Exception as e:
                logger.exception(f"Error in NATS sensor: {e}")
                return []

            finally:
                if nc:
                    await nc.close()

        run_requests = asyncio.run(check_for_events())
        yield from run_requests

    return _nats_document_uploaded_sensor
