import logging
import os
from typing import Annotated

from dagster import AssetKey, AssetSelection, Definitions, SensorDefinition
from dagster_dlt import DagsterDltResource
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.infrastructure import StructuredPipelineSettings
from swiss_ai_hub.core.persistence import SourcePipelineType

from swiss_ai_hub.pipeline.assets.factories.structured_to_data_lake.structured_sync_factory import (
    structured_sync_factory,
)
from swiss_ai_hub.pipeline.executors.factory import default_process_executor
from swiss_ai_hub.pipeline.jobs.factory import materialize_asset_job
from swiss_ai_hub.pipeline.resources.factory import default_io_manager_s3_datalake_resources
from swiss_ai_hub.pipeline.schedules.per_bucket_schedule import per_bucket_observe_schedule
from swiss_ai_hub.pipeline.sensors.run_failure_notification_sensor import run_failure_notification_sensors_from_settings
from swiss_ai_hub.pipeline.sensors.source_pipeline_registration_sensor import announced_source_pipeline_sensor
from swiss_ai_hub.pipeline.source_pipelines.structured_sync_config import StructuredSyncConfig
from swiss_ai_hub.pipeline.util.run_routing import owned_by_source

logger = logging.getLogger(__name__)

_DEFAULT_SOURCE = SourcePipelineType.STRUCTURED.value


def structured_pipeline_definitions(
    *,
    source: Annotated[str, "Source pipeline id the databases this pipeline fills point at"] = _DEFAULT_SOURCE,
    display_name: Annotated[LocaleString | None, "Localized name shown in the source selector"] = None,
    description: Annotated[LocaleString | None, "Localized description of where the records come from"] = None,
    config: Annotated[StructuredSyncConfig | None, "Form-mode config announced for this source's databases"] = None,
    settings: Annotated[StructuredPipelineSettings | None, "Schedule; read from the environment when omitted"] = None,
) -> Definitions:
    """Single deployed pipeline that syncs every knowledge database whose records come from a structured source.

    Identity-free like the rclone source pipeline: the asset graph carries no database, system or credential. The run's
    ``aihub/bucket`` tag names the database, and its source kind, credentials and scope are read from
    ``BucketEntity.source_configuration`` when the run starts. Every deployment-global name derives from ``source``.
    """
    # dlt reports anonymous usage to dlthub unless told not to; a self-hosted platform must not phone home.
    os.environ.setdefault("RUNTIME__DLTHUB_TELEMETRY", "false")
    settings = settings or StructuredPipelineSettings()
    announced_config = config or StructuredSyncConfig.as_form()

    key = AssetKey([f"{source}_source_to_datalake", "records"])
    records = structured_sync_factory(key, source=source, config_type=type(announced_config))
    sync_job = materialize_asset_job(
        source_location_name=source,
        job_name="source_sync",
        asset_selection=AssetSelection.keys(key),
        description="Syncs the knowledge database named by the run's aihub/bucket tag from its structured source.",
    )

    return Definitions(
        assets=[records],
        resources={
            "dagster_dlt": DagsterDltResource(),
            **default_io_manager_s3_datalake_resources(container_name=source),
        },
        sensors=[
            *_registration_sensors(source, display_name, description, announced_config),
            *run_failure_notification_sensors_from_settings(),
        ],
        executor=default_process_executor(),
        jobs=[sync_job],
        schedules=[
            per_bucket_observe_schedule(
                sync_job,
                owns=owned_by_source(source),
                hour=settings.OBSERVE_JOB_HOUR,
                minute=settings.OBSERVE_JOB_MINUTE,
            )
        ],
    )


def _registration_sensors(
    source: str,
    display_name: LocaleString | None,
    description: LocaleString | None,
    config: StructuredSyncConfig,
) -> list[SensorDefinition]:
    """The gate runs either way, so a bad id fails at build time; but a pipeline offering no kind is not announced,
    because the create-database dialog would show a source nothing can be configured for."""
    sensor = announced_source_pipeline_sensor(source, display_name, description, config)
    if not type(config).adapters():
        logger.warning(f"Source pipeline '{source}' offers no structured source kind yet and is not announced.")
        return []
    return [sensor]
