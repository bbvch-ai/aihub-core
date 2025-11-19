from dagster import (
    AssetKey,
    AssetMaterialization,
    DataVersionsByPartition,
    DynamicPartitionsDefinition,
    OpExecutionContext,
)

from aihub_pipeline.types.RcloneFile import MinimalRcloneFile
from aihub_pipeline.util.meta_utils import rclone_file_metadata_table
from aihub_pipeline.util.partition_utils import replace_partition_keys


def data_version_by_partition_for_rclone_files(
    context: OpExecutionContext,
    asset_key: AssetKey,
    partition: DynamicPartitionsDefinition,
    rclone_files: list[MinimalRcloneFile],
) -> DataVersionsByPartition:
    """
    Generates a dynamic partition key for each file from the rclone remote,
    reports the materialization and returns a DataVersion for each partition key.

    We use mtime + size as the version to detect when files change or are re-uploaded after deletion.
    This works consistently across all rclone-supported backends (OneDrive, SharePoint, S3, etc.).
    """
    partition_keys = [file.path for file in rclone_files]

    replace_partition_keys(
        context,
        partition.name,
        partition_keys,
    )

    context.log.info(f"Found {len(rclone_files)} files in rclone remote")
    context.log.info("Materializing external rclone source asset")

    if len(rclone_files) > 0:
        context.instance.report_runless_asset_event(
            AssetMaterialization(
                asset_key=asset_key,
                partition=rclone_files[-1].path,
                metadata={
                    "Number of Files": len(rclone_files),
                    "Total File Size (MB)": sum([file.size for file in rclone_files]) / 1e6,
                    "Table": rclone_file_metadata_table(rclone_files),
                },
            )
        )

    # Use version (timestamp-size) to detect changes
    # This ensures that if a file is deleted and re-uploaded with the same content,
    # it will be detected as a new version and trigger reprocessing
    # Using Unix timestamp (int) for consistent string representation, matching DataLake pipeline pattern
    return DataVersionsByPartition({file.path: f"{file.modified}-{file.size}" for file in rclone_files})
