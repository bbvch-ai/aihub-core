import warnings
from typing import Annotated

from dagster import (
    AssetKey,
    AssetSelection,
    Definitions,
    DynamicPartitionsDefinition,
)
from swiss_ai_hub.core.infrastructure.rclone import RcloneSourceConfig

from swiss_ai_hub.pipeline.assets.factories.local_files_system_to_data_lake.observable_local_file_system_factory import (  # noqa: E501
    observable_local_file_system_factory,
)
from swiss_ai_hub.pipeline.assets.factories.rclone_to_data_lake.observable_rclone_factory import (
    observable_rclone_factory,
)
from swiss_ai_hub.pipeline.assets.factories.share_point_to_data_lake.observable_share_point_factory import (
    observable_share_point_factory,
)
from swiss_ai_hub.pipeline.assets.factories.source_to_data_lake.data_lake_file_factory import data_lake_file_factory
from swiss_ai_hub.pipeline.assets.factories.source_to_data_lake.removed_data_lake_files_factory import (
    removed_data_lake_files_factory,
)
from swiss_ai_hub.pipeline.executors.factory import default_process_executor
from swiss_ai_hub.pipeline.io.local_file_system_io_manager import LocalFileSystemIOManager
from swiss_ai_hub.pipeline.io.rclone_io_manager import RcloneIOManager
from swiss_ai_hub.pipeline.io.share_point_io_manager import SharePointIoManager
from swiss_ai_hub.pipeline.jobs.factory import materialize_asset_job, observe_source_job
from swiss_ai_hub.pipeline.resources.factory import (
    mongo_document_store_resource,
    s3_data_lake_resources,
)
from swiss_ai_hub.pipeline.resources.local_file_system.local_file_system_resource import LocalFileSystemResource
from swiss_ai_hub.pipeline.resources.rclone.rclone_resource import RcloneResource
from swiss_ai_hub.pipeline.resources.share_point.share_point_resource import SharePointResource
from swiss_ai_hub.pipeline.schedules.factory import daily_schedule_at
from swiss_ai_hub.pipeline.sensors.factory import default_automation_sensor
from swiss_ai_hub.pipeline.sensors.run_after_success_sensor import run_after_success_sensor
from swiss_ai_hub.pipeline.sensors.run_failure_notification_sensor import (
    run_failure_notification_sensors_from_settings,
)
from swiss_ai_hub.pipeline.util.bucket_utils import get_db_name_from_bucket_name


def default_sharepoint_to_datalake_definitions(
    *,
    datalake_container_name: Annotated[str, "S3 bucket/container name where SharePoint files will be uploaded"],
    datalake_directory_name: Annotated[str | None, "Optional subdirectory within container"] = None,
    target_folders: Annotated[list[str] | None, "List of SharePoint folder paths to sync"] = None,
    exclude_folders: Annotated[list[str] | None, "List of SharePoint folder paths to exclude"] = None,
    supported_filetypes: Annotated[list[str] | None, "List of file extensions to sync"] = None,
    observe_job_hour: Annotated[int, "Hour to run daily SharePoint observation job"] = 0,
    observe_job_minute: Annotated[int, "Minute to run daily SharePoint observation job"] = 0,
    max_partitions: Annotated[int, "Maximum number of partitions to create or delete at once"] = 1000,
) -> Definitions:
    """
    Creates a SharePoint to DataLake pipeline using local S3-compatible storage.

    Use this when you need to sync corporate documents from SharePoint to your local data lake.
    The pipeline monitors SharePoint for changes and automatically downloads new/updated files
    to your local S3 storage. It handles authentication, filtering, and cleanup of deleted files.

    Pipeline: SharePoint → S3

    This is the first step - combine with document_ingestion_pipeline_definitions() to process
    files into embeddings for semantic retrieval.
    """
    sharepoint_partitions = DynamicPartitionsDefinition(name=f"{datalake_container_name}_sharepoint_partitions")

    sharepoint_key = AssetKey([datalake_container_name, "sharepoint_to_datalake", "sharepoint"])
    data_lake_files_key = AssetKey([datalake_container_name, "sharepoint_to_datalake", "data_lake_files"])
    removed_data_lake_files_key = AssetKey(
        [datalake_container_name, "sharepoint_to_datalake", "removed_data_lake_files"]
    )

    observable_sharepoint_asset = observable_share_point_factory(sharepoint_key, sharepoint_partitions, max_partitions)

    assets = [
        observable_sharepoint_asset,
        data_lake_file_factory(
            key=data_lake_files_key,
            source_key=sharepoint_key,
            partitions=sharepoint_partitions,
        ),
        removed_data_lake_files_factory(
            key=removed_data_lake_files_key,
            source_key=sharepoint_key,
        ),
    ]

    observe_job = observe_source_job(
        observable_asset=observable_sharepoint_asset,
        source_location_name=datalake_container_name,
    )

    remove_job = materialize_asset_job(
        source_location_name=datalake_container_name,
        job_name="remove_sharepoint_files",
        asset_selection=AssetSelection.keys(removed_data_lake_files_key),
    )

    sharepoint_client = SharePointResource(
        target_folders=target_folders,
        exclude_folders=exclude_folders,
        supported_filetypes=supported_filetypes,
    )

    sharepoint_io_manager = SharePointIoManager(share_point_client=sharepoint_client)

    store_name = get_db_name_from_bucket_name(bucket_name=datalake_container_name, auto_sync=False)

    return Definitions(
        assets=assets,
        resources={
            "share_point_client": sharepoint_client,
            "sharepoint_io_manager": sharepoint_io_manager,
            **s3_data_lake_resources(
                container_name=datalake_container_name,
                directory_name=datalake_directory_name,
            ),
            **mongo_document_store_resource(document_store_name=store_name),
        },
        sensors=[
            default_automation_sensor(assets),
            run_after_success_sensor(monitored_job=observe_job, triggered_job=remove_job),
            *run_failure_notification_sensors_from_settings(),
        ],
        executor=default_process_executor(),
        jobs=[observe_job, remove_job],
        schedules=[daily_schedule_at(observe_job, hour=observe_job_hour, minute=observe_job_minute)],
    )


def default_local_filesystem_to_datalake_definitions(
    *,
    datalake_container_name: Annotated[str, "S3 bucket/container name where local filesystem files will be uploaded"],
    base_path: Annotated[str, "Root directory path to scan for files"],
    include_patterns: Annotated[list[str] | None, "List of patterns to include"] = None,
    datalake_directory_name: Annotated[str | None, "Optional subdirectory within container"] = None,
    exclude_patterns: Annotated[list[str] | None, "List of patterns to exclude"] = None,
    observe_job_hour: Annotated[int, "Hour to run daily filesystem observation job"] = 0,
    observe_job_minute: Annotated[int, "Minute to run daily filesystem observation job"] = 0,
    max_partitions: Annotated[int, "Maximum number of partitions to create or delete at once"] = 1000,
    encode_partition_keys: Annotated[
        bool | None,
        "URL-encode special characters in partition keys. Will default to True in a future version.",
    ] = None,
) -> Definitions:
    """
    Creates a Local File System to DataLake pipeline using S3-compatible storage.

    Use this when you need to sync files from a local or network file system to your data lake.
    The pipeline monitors specified directories for changes and automatically uploads new/updated files
    to your S3 storage. It handles flexible pattern-based file filtering, folder organization,
    and cleanup of deleted files.

    All filtering uses regex patterns for maximum flexibility. Use helper functions from
    swiss_ai_hub.pipeline.util.pattern_utils to convert lists to patterns:
    - exact_match_pattern(["A", "B"]) for exact folder names
    - extension_pattern([".pdf", ".docx"]) for file extensions
    - contains_pattern("archive") for substring matching

    Pipeline: Local File System → S3

    This is the first step - combine with document_ingestion_pipeline_definitions() to process
    files into embeddings for semantic retrieval.
    """
    encode = resolve_encode_partition_keys(encode_partition_keys)

    filesystem_partitions = DynamicPartitionsDefinition(name=f"{datalake_container_name}_local_fs_partitions")

    filesystem_key = AssetKey([datalake_container_name, "local_fs_to_datalake", "local_fs"])
    data_lake_files_key = AssetKey([datalake_container_name, "local_fs_to_datalake", "data_lake_files"])
    removed_data_lake_files_key = AssetKey([datalake_container_name, "local_fs_to_datalake", "removed_data_lake_files"])

    observable_filesystem_asset = observable_local_file_system_factory(
        filesystem_key,
        filesystem_partitions,
        max_partitions,
        encode_partition_keys=encode,
    )

    assets = [
        observable_filesystem_asset,
        data_lake_file_factory(
            key=data_lake_files_key,
            source_key=filesystem_key,
            partitions=filesystem_partitions,
        ),
        removed_data_lake_files_factory(
            key=removed_data_lake_files_key,
            source_key=filesystem_key,
        ),
    ]

    observe_job = observe_source_job(
        observable_asset=observable_filesystem_asset,
        source_location_name=datalake_container_name,
    )

    remove_job = materialize_asset_job(
        source_location_name=datalake_container_name,
        job_name="remove_filesystem_files",
        asset_selection=AssetSelection.keys(removed_data_lake_files_key),
    )

    filesystem_client = LocalFileSystemResource(
        base_path=base_path,
        include_patterns=include_patterns,
        exclude_patterns=exclude_patterns,
    )

    filesystem_io_manager = LocalFileSystemIOManager(
        local_file_system_client=filesystem_client,
        encode_partition_keys=encode,
    )

    store_name = get_db_name_from_bucket_name(bucket_name=datalake_container_name, auto_sync=True)

    return Definitions(
        assets=assets,
        resources={
            "local_file_system_client": filesystem_client,
            "local_file_system_io_manager": filesystem_io_manager,
            **s3_data_lake_resources(
                container_name=datalake_container_name,
                directory_name=datalake_directory_name,
                encode_partition_keys=encode,
            ),
            **mongo_document_store_resource(document_store_name=store_name),
        },
        sensors=[
            default_automation_sensor(assets),
            run_after_success_sensor(monitored_job=observe_job, triggered_job=remove_job),
            *run_failure_notification_sensors_from_settings(),
        ],
        executor=default_process_executor(),
        jobs=[observe_job, remove_job],
        schedules=[daily_schedule_at(observe_job, hour=observe_job_hour, minute=observe_job_minute)],
    )


def default_rclone_to_datalake_definitions(
    *,
    datalake_container_name: Annotated[str, "S3 bucket/container name where rclone files will be uploaded"],
    source_remote: Annotated[
        str, "Rclone remote name and path (e.g., 'onedrive:Documents', 's3:bucket/prefix', 'gdrive:MyFolder')"
    ],
    rclone_config: Annotated[RcloneSourceConfig | None, "Rclone configurations"] = None,
    datalake_directory_name: Annotated[str | None, "Optional subdirectory within container"] = None,
    include_patterns: Annotated[
        list[str] | None, "Include patterns using rclone glob syntax (e.g., ['*.pdf', '*.docx'])"
    ] = None,
    exclude_patterns: Annotated[
        list[str] | None, "Exclude patterns using rclone glob syntax (e.g., ['**/archiv/**', '**/temp/**'])"
    ] = None,
    observe_job_hour: Annotated[int, "Hour to run daily rclone observation job"] = 0,
    observe_job_minute: Annotated[int, "Minute to run daily rclone observation job"] = 0,
    max_partitions: Annotated[int, "Maximum number of partitions to create or delete at once"] = 1000,
    encode_partition_keys: Annotated[
        bool | None,
        "URL-encode special characters in partition keys. Will default to True in a future version.",
    ] = None,
) -> Definitions:
    """
    Creates an Rclone to DataLake pipeline using S3-compatible storage.

    Use this when you need to sync files from ANY rclone-supported backend (70+ providers)
    to your data lake. Works with OneDrive, SharePoint, S3, Azure Blob, Google Drive,
    Dropbox, Box, local filesystem, and many more.

    The pipeline monitors the rclone remote for changes and automatically downloads new/updated
    files to your S3 storage. It handles authentication via rclone config, filtering, and
    cleanup of deleted files.

    **Why rclone**: Single implementation works across all cloud storage providers without
    provider-specific SDKs or custom authentication code.

    **Setup**: Requires rclone binary installed and configured. Use 'rclone config' or
    environment variables to set up remotes.

    Pipeline: Rclone Remote (OneDrive/SharePoint/S3/Azure/GDrive/etc.) → S3

    This is the first step - combine with document_ingestion_pipeline_definitions() to process
    files into embeddings for semantic retrieval.

    Example:
        # OneDrive to S3
        defs = default_rclone_to_datalake_definitions(
            datalake_container_name="my-company-docs",
            source_remote="onedrive:Documents",
            include_patterns=["*.pdf", "*.docx"],
            exclude_patterns=["**/archive/**"],
        )

        # Google Drive to S3
        defs = default_rclone_to_datalake_definitions(
            datalake_container_name="gdrive-sync",
            source_remote="gdrive:Shared Documents",
            include_patterns=["*.pdf"],
        )
    """
    encode = resolve_encode_partition_keys(encode_partition_keys)

    # Extract source name from config or from source_remote (e.g., "onedrive:Documents" -> "onedrive")
    # Ensure we always derive a non-empty, stable source_name for asset keys
    if rclone_config and rclone_config.name:
        source_name = rclone_config.name
    else:
        # Extract remote name before the colon if present and non-empty; otherwise use local_fs fallback
        source_remote_str = (source_remote or "").strip()
        if ":" in source_remote_str:
            candidate = source_remote_str.split(":", 1)[0].strip()
            source_name = candidate if candidate else "local_fs"
        else:
            source_name = "local_fs"

    rclone_partitions = DynamicPartitionsDefinition(name=f"{datalake_container_name}_{source_name}_rclone_partitions")

    pipeline_group = f"{source_name}_to_datalake"

    rclone_key = AssetKey([datalake_container_name, pipeline_group, source_name])
    data_lake_files_key = AssetKey([datalake_container_name, pipeline_group, "data_lake_files"])
    removed_data_lake_files_key = AssetKey([datalake_container_name, pipeline_group, "removed_data_lake_files"])

    observable_rclone_asset = observable_rclone_factory(
        rclone_key, rclone_partitions, max_partitions, encode_partition_keys=encode
    )

    assets = [
        observable_rclone_asset,
        data_lake_file_factory(
            key=data_lake_files_key,
            source_key=rclone_key,
            partitions=rclone_partitions,
        ),
        removed_data_lake_files_factory(
            key=removed_data_lake_files_key,
            source_key=rclone_key,
        ),
    ]

    observe_job = observe_source_job(
        observable_asset=observable_rclone_asset,
        source_location_name=datalake_container_name,
    )

    remove_job = materialize_asset_job(
        source_location_name=datalake_container_name,
        job_name="remove_rclone_files",
        asset_selection=AssetSelection.keys(removed_data_lake_files_key),
    )

    rclone_client = RcloneResource(
        source_remote=source_remote,
        include_patterns=include_patterns,
        exclude_patterns=exclude_patterns,
        rclone_config_dict=rclone_config.model_dump(mode="json", exclude_none=True) if rclone_config else None,
    )

    rclone_io_manager = RcloneIOManager(rclone_client=rclone_client, encode_partition_keys=encode)

    store_name = get_db_name_from_bucket_name(bucket_name=datalake_container_name, auto_sync=True)

    return Definitions(
        assets=assets,
        resources={
            "rclone_client": rclone_client,
            "rclone_io_manager": rclone_io_manager,
            **s3_data_lake_resources(
                container_name=datalake_container_name,
                directory_name=datalake_directory_name,
                encode_partition_keys=encode,
            ),
            **mongo_document_store_resource(document_store_name=store_name),
        },
        sensors=[
            default_automation_sensor(assets),
            run_after_success_sensor(monitored_job=observe_job, triggered_job=remove_job),
            *run_failure_notification_sensors_from_settings(),
        ],
        executor=default_process_executor(),
        jobs=[observe_job, remove_job],
        schedules=[daily_schedule_at(observe_job, hour=observe_job_hour, minute=observe_job_minute)],
    )


def resolve_encode_partition_keys(value: bool | None) -> bool:
    """Resolve encode_partition_keys for S3-based pipelines, emitting a deprecation warning when unset.

    Only applies to pipelines that use file paths as partition keys (local filesystem, rclone, S3 data lake).
    SharePoint pipelines use opaque item IDs that need no encoding. The Azure Data Lake IO manager is not
    wired through definition builders (manual assembly only) and will be added when needed.
    """
    if value is not None:
        return value
    warnings.warn(
        "encode_partition_keys is not set and defaults to False. "
        "In a future version it will default to True, which URL-encodes special characters "
        "in Dagster partition keys but invalidates existing partitions (triggering full re-processing). "
        "Set encode_partition_keys=False explicitly to keep the current behavior, "
        "or set encode_partition_keys=True to opt in now.",
        DeprecationWarning,
        stacklevel=3,
    )
    return False
