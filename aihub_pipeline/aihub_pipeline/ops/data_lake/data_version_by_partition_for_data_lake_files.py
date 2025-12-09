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
) -> DataVersionsByPartition:
    """Generates a dynamic partition key for each file in the data lake, reports the data lake materialization
    and returns a DataVersion for each partition key.
    """
    replace_partition_keys(
        context,
        partition.name,
        [data_lake_file.uri for data_lake_file in data_lake_files],
        max_partitions=max_partitions,
    )
    context.log.info(f"Found {len(data_lake_files)} files in the data lake")
    context.log.info("Materializing external data lake asset")
    if len(data_lake_files) > 0:
        context.instance.report_runless_asset_event(
            AssetMaterialization(
                asset_key=asset_key,
                partition=data_lake_files[-1].uri,
                metadata={
                    "Number of Files": len(data_lake_files),
                    "Total File Size (MB)": sum([data_lake_file.size for data_lake_file in data_lake_files]) / 1e6,
                    "Table": data_lake_metadata_table(data_lake_files),
                },
            )
        )

    # We need to incorporate the updated timestamp into the version key to ensure that a file that is deleted
    # from the data lake and then inserted again with the exact same content will be detected as a new version
    # and trigger a reprocessing of the document.
    # If we just take the file hash, dagster thinks that this file was already processed and will not trigger
    # a reprocessing, because dagster is not aware that we deleted the file in the meantime.
    # I tried to overcome this using wipe_asset_partitions (https://docs.dagster.io/_modules/dagster/_core/instance)
    # but this is currently only available in Dagster+ (https://github.com/dagster-io/dagster/issues/14749)
    # Hence, when the issue is resolved, we can wipe the materialized asset when we delete it and hence
    # get rid of the need to incorporate the updated timestamp into the version key, as dagster will "forget"
    # that the asset ever existed and re-process it when it is encountered again.
    existing_partitions = set(context.instance.get_dynamic_partitions(partition.name))
    files_with_partitions = [
        data_lake_file for data_lake_file in data_lake_files if data_lake_file.uri in existing_partitions
    ]

    return DataVersionsByPartition(
        {
            data_lake_file.uri: f"{data_lake_file.updated}-{data_lake_file.hash}"
            for data_lake_file in files_with_partitions
        }
    )
