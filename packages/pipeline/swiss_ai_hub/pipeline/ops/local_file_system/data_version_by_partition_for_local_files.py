from dagster import (
    AssetKey,
    AssetMaterialization,
    DataVersionsByPartition,
    DynamicPartitionsDefinition,
    OpExecutionContext,
)
from swiss_ai_hub.core.generative_ai.utils.path_utils import encode_partition_key

from swiss_ai_hub.pipeline.types.SourceFile import MinimalSourceFile
from swiss_ai_hub.pipeline.util.meta_utils import local_file_metadata_table
from swiss_ai_hub.pipeline.util.partition_utils import replace_partition_keys


def data_version_by_partition_for_local_files(
    context: OpExecutionContext,
    asset_key: AssetKey,
    partition: DynamicPartitionsDefinition,
    local_files: list[MinimalSourceFile],
    max_partitions: int,
    encode_partition_keys: bool = False,
) -> DataVersionsByPartition:
    """
    Generates a dynamic partition key for each file in the local filesystem,
    reports the materialization and returns a DataVersion for each partition key.

    When ``encode_partition_keys`` is True, partition keys are URL-encoded to avoid
    issues with special characters in Dagster. Decoding recovers the exact original path.
    We use mtime + size as the version to detect when files change or are re-uploaded after deletion.
    """
    make_key = encode_partition_key if encode_partition_keys else lambda v: v
    key_by_path = {file.path: make_key(file.path) for file in local_files}
    partition_keys = list(key_by_path.values())

    replace_partition_keys(
        context,
        partition.name,
        partition_keys,
        max_partitions=max_partitions,
    )

    context.log.info(f"Found {len(local_files)} files in the local filesystem")
    context.log.info("Materializing external local filesystem asset")

    if len(local_files) > 0:
        context.instance.report_runless_asset_event(
            AssetMaterialization(
                asset_key=asset_key,
                partition=key_by_path[local_files[-1].path],
                metadata={
                    "Number of Files": len(local_files),
                    "Total File Size (MB)": sum([file.size for file in local_files]) / 1e6,
                    "Table": local_file_metadata_table(local_files),
                },
            )
        )

    # Version includes timestamp so re-uploaded files trigger reprocessing
    existing_partitions = set(context.instance.get_dynamic_partitions(partition.name))
    files_with_partitions = [
        local_file for local_file in local_files if key_by_path[local_file.path] in existing_partitions
    ]

    return DataVersionsByPartition(
        {
            key_by_path[local_file.path]: f"{local_file.modified}-{local_file.size}"
            for local_file in files_with_partitions
        }
    )
