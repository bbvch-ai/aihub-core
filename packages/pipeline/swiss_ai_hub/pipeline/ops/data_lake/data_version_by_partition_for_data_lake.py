from dagster import (
    AssetKey,
    AssetMaterialization,
    DataVersionsByPartition,
    DynamicPartitionsDefinition,
    OpExecutionContext,
)

from swiss_ai_hub.pipeline.types.data_lake_file import DataLakeFile
from swiss_ai_hub.pipeline.util.meta_utils import data_lake_metadata_table
from swiss_ai_hub.pipeline.util.partition_utils import make_composite_partition_key, replace_partition_keys_for_bucket


def data_version_by_partition_for_data_lake_no_op(
    context: OpExecutionContext,
    asset_key: AssetKey,
    partition: DynamicPartitionsDefinition,
    bucket: str,
    data_lake_files: list[DataLakeFile],
    max_partitions: int,
    encode_partition_keys: bool = True,
) -> DataVersionsByPartition:
    """Route-per-run variant of ``data_version_by_partition_for_data_lake_files_no_op``.

    The RAG pipeline shares one partition registry across all knowledge databases, so partition keys
    are composite ``{bucket}|{file_uri}`` and reconciliation is scoped to the run's bucket via
    ``replace_partition_keys_for_bucket`` — one bucket's observe run can never delete another's partitions.
    """
    key_by_uri = {
        file.uri: make_composite_partition_key(bucket, file.uri, encode=encode_partition_keys)
        for file in data_lake_files
    }
    partition_keys = list(key_by_uri.values())

    replace_partition_keys_for_bucket(
        context,
        partition.name,
        bucket,
        partition_keys,
        max_partitions=max_partitions,
    )
    context.log.info(f"Found {len(data_lake_files)} files in the data lake for bucket '{bucket}'")
    if data_lake_files:
        context.instance.report_runless_asset_event(
            AssetMaterialization(
                asset_key=asset_key,
                partition=key_by_uri[data_lake_files[-1].uri],
                metadata={
                    "Bucket": bucket,
                    "Number of Files": len(data_lake_files),
                    "Total File Size (MB)": sum(data_lake_file.size for data_lake_file in data_lake_files) / 1e6,
                    "Table": data_lake_metadata_table(data_lake_files),
                },
            )
        )

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
