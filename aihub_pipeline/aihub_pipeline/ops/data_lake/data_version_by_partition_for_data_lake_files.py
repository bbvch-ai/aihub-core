from aihub_lib.generative_ai.utils.path_utils import encode_partition_key
from dagster import (
    AssetKey,
    AssetMaterialization,
    DataVersionsByPartition,
    DynamicPartitionsDefinition,
    OpExecutionContext,
)

from aihub_pipeline.types.DataLakeFile import DataLakeFile
from aihub_pipeline.util.meta_utils import data_lake_metadata_table
from aihub_pipeline.util.partition_utils import replace_partition_keys


def data_version_by_partition_for_data_lake_files_no_op(
    context: OpExecutionContext,
    asset_key: AssetKey,
    partition: DynamicPartitionsDefinition,
    data_lake_files: list[DataLakeFile],
    max_partitions: int,
    encode_partition_keys: bool = False,
) -> DataVersionsByPartition:
    """Generates a dynamic partition key for each file in the data lake, reports the data lake materialization
    and returns a DataVersion for each partition key.

    When ``encode_partition_keys`` is True, partition keys are URL-encoded to avoid
    issues with special characters in Dagster. Decoding recovers the exact original path.
    """
    make_key = encode_partition_key if encode_partition_keys else lambda v: v
    key_by_uri = {file.uri: make_key(file.uri) for file in data_lake_files}
    partition_keys = list(key_by_uri.values())

    replace_partition_keys(
        context,
        partition.name,
        partition_keys,
        max_partitions=max_partitions,
    )
    context.log.info(f"Found {len(data_lake_files)} files in the data lake")
    context.log.info("Materializing external data lake asset")
    if len(data_lake_files) > 0:
        context.instance.report_runless_asset_event(
            AssetMaterialization(
                asset_key=asset_key,
                partition=key_by_uri[data_lake_files[-1].uri],
                metadata={
                    "Number of Files": len(data_lake_files),
                    "Total File Size (MB)": sum([data_lake_file.size for data_lake_file in data_lake_files]) / 1e6,
                    "Table": data_lake_metadata_table(data_lake_files),
                },
            )
        )

    # Version includes timestamp so re-uploaded files trigger reprocessing
    existing_partitions = set(context.instance.get_dynamic_partitions(partition.name))
    files_with_partitions = [
        data_lake_file for data_lake_file in data_lake_files if key_by_uri[data_lake_file.uri] in existing_partitions
    ]

    return DataVersionsByPartition(
        {
            key_by_uri[data_lake_file.uri]: f"{data_lake_file.updated}-{data_lake_file.hash}"
            for data_lake_file in files_with_partitions
        }
    )
