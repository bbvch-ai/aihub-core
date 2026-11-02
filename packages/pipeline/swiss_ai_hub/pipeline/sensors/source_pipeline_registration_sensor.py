from typing import Annotated

from dagster import DefaultSensorStatus, SensorDefinition, SensorEvaluationContext, SkipReason, sensor
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.persistence import SourcePipeline, SourcePipelineEntity, SourcePipelineType
from swiss_ai_hub.core.source_pipelines import SourcePipelineConfig

from swiss_ai_hub.pipeline.util.bucket_utils import ensure_main_db_connection

_REGISTRATION_INTERVAL_SECONDS = 300


def announced_source_pipeline_sensor(
    source: Annotated[str, "Source pipeline id the databases this pipeline fills point at"],
    display_name: Annotated[LocaleString | None, "Localized name shown in the source selector"],
    description: Annotated[LocaleString | None, "Localized description of where the records or files come from"],
    config: Annotated[SourcePipelineConfig, "Form-mode config announced for this source's databases"],
) -> SensorDefinition:
    """The registration sensor every source pipeline builds through, so they share one gate.

    Mirrors the ingestion pipeline's gate: reserved ids fail at build time, and only a shipped source may rely on
    the platform's translations for its labels.
    """
    if source in SourcePipelineEntity.reserved_ids():
        msg = f"Source pipeline id '{source}' is reserved by the platform and cannot be claimed by a pipeline."
        raise ValueError(msg)
    if source in {source_type.value for source_type in SourcePipelineType}:
        display_name = display_name or LocaleString.from_i18n_path(f"lib.source_pipelines.{source}.display_name")
        description = description or LocaleString.from_i18n_path(f"lib.source_pipelines.{source}.description")
    if display_name is None or description is None:
        msg = f"Custom source pipeline '{source}' needs a display_name and a description to be selectable."
        raise ValueError(msg)
    return source_pipeline_registration_sensor(SourcePipeline.from_config(source, display_name, description, config))


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
