from dagster import DefaultSensorStatus, sensor
from dagster._core.definitions.target import ExecutableDefinition

from aihub_lib.nats.topics.pipeline.PipelineTopic import PipelineTopic


def nats_document_uploaded_sensor(
    job: ExecutableDefinition,
    pipeline_topic: PipelineTopic,
):
    @sensor(
        job=job,
        minimum_interval_seconds=5,
        default_status=DefaultSensorStatus.RUNNING,
    )
    def _():
        pass

    return _
