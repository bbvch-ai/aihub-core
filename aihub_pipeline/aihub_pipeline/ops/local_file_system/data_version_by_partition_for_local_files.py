from dagster import (
    AssetKey,
    AssetMaterialization,
    DataVersionsByPartition,
    DynamicPartitionsDefinition,
    OpExecutionContext,
)

from aihub_pipeline.types.SourceFile import MinimalSourceFile
from aihub_pipeline.util.meta_utils import local_file_metadata_table
from aihub_pipeline.util.partition_utils import replace_partition_keys


def data_version_by_partition_for_local_files(
    context: OpExecutionContext,
    asset_key: AssetKey,
    partition: DynamicPartitionsDefinition,
    local_files: list[MinimalSourceFile],
    max_partitions: int,
) -> DataVersionsByPartition:
    """
    Generates a dynamic partition key for each file in the local filesystem,
    reports the materialization and returns a DataVersion for each partition key.

    We use mtime + size as the version to detect when files change or are re-uploaded after deletion.
    """
    partition_keys = [file.path for file in local_files]

    replace_partition_keys(
        context,
        partition.name,
        partition_keys,
        max_partitions,
    )

    context.log.info(f"Found {len(local_files)} files in the local filesystem")
    context.log.info("Materializing external local filesystem asset")

    if len(local_files) > 0:
        context.instance.report_runless_asset_event(
            AssetMaterialization(
                asset_key=asset_key,
                partition=local_files[-1].path,
                metadata={
                    "Number of Files": len(local_files),
                    "Total File Size (MB)": sum([file.size for file in local_files]) / 1e6,
                    "Table": local_file_metadata_table(local_files),
                },
            )
        )

    # Use version (timestamp-size) to detect changes
    # This ensures that if a file is deleted and re-uploaded with the same content,
    # it will be detected as a new version and trigger reprocessing
    # Using Unix timestamp (int) for consistent string representation, matching DataLake pipeline pattern
    existing_partitions = set(context.instance.get_dynamic_partitions(partition.name))
    files_with_partitions = [file for file in local_files if file.path in existing_partitions]

    return DataVersionsByPartition(
        {file.path: f"{file.modified}-{file.size}" for file in files_with_partitions}  # Only files with partitions
    )
