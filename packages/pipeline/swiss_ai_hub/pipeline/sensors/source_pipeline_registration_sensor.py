from typing import Annotated

from dagster import DefaultSensorStatus, SensorDefinition, SensorEvaluationContext, SkipReason, sensor
from swiss_ai_hub.core.persistence import SourcePipeline, SourcePipelineEntity

from swiss_ai_hub.pipeline.util.bucket_utils import ensure_main_db_connection

_REGISTRATION_INTERVAL_SECONDS = 300


def source_pipeline_registration_sensor(
    source_pipeline: Annotated[SourcePipeline, "This pipeline's labels, form and schema"],
) -> SensorDefinition:
    """Advertises this pipeline as a selectable source, with the form a database's source is configured through.

    The Stage-1 counterpart of ``ingestor_registration_sensor``: written to the database the API already reads
    rather than broadcast, from a sensor rather than at import so a Mongo outage cannot take the code location
    down.
    """

    @sensor(
        minimum_interval_seconds=_REGISTRATION_INTERVAL_SECONDS,
        default_status=DefaultSensorStatus.RUNNING,
        name=f"SourcePipelineRegistrationSensorFor_{source_pipeline.id}",
        description="Keeps this pipeline listed as a selectable source, with its configuration form, for new "
        "knowledge databases.",
    )
    def _sensor(context: SensorEvaluationContext) -> SkipReason:
        ensure_main_db_connection()
        SourcePipelineEntity.upsert(source_pipeline)
        return SkipReason(f"Source pipeline '{source_pipeline.id}' is registered.")

    return _sensor
