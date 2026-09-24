from typing import Annotated

from dagster import AssetKey, AssetSelection, Definitions, DynamicPartitionsDefinition, SensorDefinition
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.infrastructure import RclonePipelineSettings
from swiss_ai_hub.core.persistence import SourcePipeline, SourcePipelineEntity, SourcePipelineType
from swiss_ai_hub.core.source_pipelines import SourcePipelineConfig

from swiss_ai_hub.pipeline.assets.factories.rclone_to_data_lake.observable_rclone_factory import (
    observable_rclone_factory,
)
from swiss_ai_hub.pipeline.assets.factories.source_to_data_lake.routed_data_lake_file_factory import (
    routed_data_lake_file_factory,
)
from swiss_ai_hub.pipeline.assets.factories.source_to_data_lake.routed_removed_data_lake_files_factory import (
    routed_removed_data_lake_files_factory,
)
from swiss_ai_hub.pipeline.executors.factory import default_process_executor
from swiss_ai_hub.pipeline.io.routed_rclone_io_manager import RoutedRcloneIOManager
from swiss_ai_hub.pipeline.jobs.factory import materialize_asset_job, observe_source_job
from swiss_ai_hub.pipeline.resources.factory import default_io_manager_s3_datalake_resources
from swiss_ai_hub.pipeline.schedules.per_bucket_schedule import per_bucket_observe_schedule
from swiss_ai_hub.pipeline.sensors.factory import default_automation_sensor
from swiss_ai_hub.pipeline.sensors.run_after_success_sensor import run_after_success_sensor
from swiss_ai_hub.pipeline.sensors.run_failure_notification_sensor import run_failure_notification_sensors_from_settings
from swiss_ai_hub.pipeline.sensors.source_bucket_cleanup_sensor import source_bucket_cleanup_sensor
from swiss_ai_hub.pipeline.sensors.source_pipeline_registration_sensor import source_pipeline_registration_sensor
from swiss_ai_hub.pipeline.source_pipelines.rclone_sync_config import RcloneSyncConfig
from swiss_ai_hub.pipeline.util.run_routing import owned_by_source

_DEFAULT_SOURCE = SourcePipelineType.RCLONE.value


def rclone_pipeline_definitions(
    *,
    source: Annotated[str, "Source pipeline id the databases this pipeline fills point at"] = _DEFAULT_SOURCE,
    display_name: Annotated[LocaleString | None, "Localized name shown in the source selector"] = None,
    description: Annotated[LocaleString | None, "Localized description of where the files come from"] = None,
    config: Annotated[SourcePipelineConfig | None, "Form-mode config announced for this source's databases"] = None,
    settings: Annotated[RclonePipelineSettings | None, "Schedule; read from the environment when omitted"] = None,
) -> Definitions:
    """Single deployed pipeline that syncs every knowledge database sourced from rclone (Stage 1: source → data lake).

    Identity-free like the document ingestion pipeline: the asset graph carries no bucket, remote or credential.
    The target database is resolved per run — from the ``aihub/bucket`` run tag on the observe/remove path, from
    the composite ``{bucket}|{path}`` partition key on the write path — and its backend, credentials, root path and
    patterns are read from ``BucketEntity.source_configuration`` at that moment. A database created or re-credentialed
    after deployment is picked up on the next tick, with no code-location reload.

    Every deployment-global name derives from ``source``, with suffixes distinct from the ingestion pipeline's, so
    the two families and any second source pipeline never collide on asset keys, partition registries or job names.
    """
    settings = settings or RclonePipelineSettings()

    asset_group = f"{source}_source_to_datalake"
    remote_files_key = AssetKey([asset_group, "remote_files"])
    data_lake_files_key = AssetKey([asset_group, "data_lake_files"])
    removed_files_key = AssetKey([asset_group, "removed_data_lake_files"])
    partitions = DynamicPartitionsDefinition(name=f"{source}_source_partitions")

    observable_asset = observable_rclone_factory(
        remote_files_key, partitions, source=source, max_partitions=settings.MAX_PARTITIONS
    )
    assets = [
        observable_asset,
        routed_data_lake_file_factory(data_lake_files_key, source_key=remote_files_key, partitions=partitions),
        routed_removed_data_lake_files_factory(removed_files_key, source_key=remote_files_key),
    ]

    observe_job = observe_source_job(observable_asset=observable_asset, source_location_name=source)
    remove_job = materialize_asset_job(
        source_location_name=source,
        job_name="remove_source_files",
        asset_selection=AssetSelection.keys(removed_files_key),
    )

    announced_config = config or RcloneSyncConfig.as_form()
    registration_sensor = _registration_sensor(source, display_name, description, announced_config)

    return Definitions(
        assets=assets,
        resources={
            "rclone_io_manager": RoutedRcloneIOManager(source=source),
            **default_io_manager_s3_datalake_resources(container_name=source),
        },
        sensors=[
            default_automation_sensor(assets),
            run_after_success_sensor(monitored_job=observe_job, triggered_job=remove_job, require_bucket_tag=True),
            registration_sensor,
            source_bucket_cleanup_sensor(source=source, partition_registry_name=partitions.name),
            *run_failure_notification_sensors_from_settings(),
        ],
        executor=default_process_executor(),
        jobs=[observe_job, remove_job],
        schedules=[
            per_bucket_observe_schedule(
                observe_job,
                owns=owned_by_source(source),
                hour=settings.OBSERVE_JOB_HOUR,
                minute=settings.OBSERVE_JOB_MINUTE,
            )
        ],
    )


def _registration_sensor(
    source: str,
    display_name: LocaleString | None,
    description: LocaleString | None,
    config: SourcePipelineConfig,
) -> SensorDefinition:
    """Mirrors the ingestion pipeline's gate: reserved ids fail at build time, only the shipped source may rely on the
    platform's translations for its labels."""
    if source in SourcePipelineEntity.reserved_ids():
        msg = f"Source pipeline id '{source}' is reserved by the platform and cannot be claimed by a pipeline."
        raise ValueError(msg)
    if source == SourcePipelineType.RCLONE.value:
        display_name = display_name or LocaleString.from_i18n_path("lib.source_pipelines.rclone.display_name")
        description = description or LocaleString.from_i18n_path("lib.source_pipelines.rclone.description")
    if display_name is None or description is None:
        msg = f"Custom source pipeline '{source}' needs a display_name and a description to be selectable."
        raise ValueError(msg)
    return source_pipeline_registration_sensor(SourcePipeline.from_config(source, display_name, description, config))
