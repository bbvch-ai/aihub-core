from dagster import (
    AssetKey,
    DataVersionsByPartition,
    DynamicPartitionsDefinition,
    OpExecutionContext,
    ResourceParam,
    observable_source_asset,
)

from swiss_ai_hub.pipeline.ops.data_lake.data_version_by_partition_for_data_lake_files import (
    data_version_by_partition_for_data_lake_files_no_op,
)
from swiss_ai_hub.pipeline.ops.data_lake.fetch_all_files_in_data_lake import fetch_all_files_in_data_lake_no_op
from swiss_ai_hub.pipeline.resources.data_lake.base.AbstractDataLakeClient import AbstractDataLakeClient
from swiss_ai_hub.pipeline.types.DataLakeFile import DataLakeFile
from swiss_ai_hub.pipeline.util.key_utils import group_name_from_asset_key


def observable_data_lake_factory(
    key: AssetKey,
    partitions: DynamicPartitionsDefinition,
    max_partitions: int,
    encode_partition_keys: bool = False,
) -> observable_source_asset:
    """Creates an observable source asset representing a data lake containing files that should be processed
    by the pipeline. The asset generates a partition for each file in the data lake as well as a DataVersion
    key based on the file content hash.
    """

    @observable_source_asset(
        key=key,
        group_name=group_name_from_asset_key(key),
        partitions_def=partitions,
        io_manager_key="data_lake_io_manager",
        description="Observes the data lake for any changes with respect to the Document Store",
    )
    def observable_data_lake(
        context: OpExecutionContext,
        data_lake_client: ResourceParam[AbstractDataLakeClient],
    ) -> DataVersionsByPartition:
        data_lake_files: list[DataLakeFile] = fetch_all_files_in_data_lake_no_op(
            data_lake_client=data_lake_client,
        )
        return data_version_by_partition_for_data_lake_files_no_op(
            context=context,
            asset_key=key,
            partition=partitions,
            data_lake_files=data_lake_files,
            max_partitions=max_partitions,
            encode_partition_keys=encode_partition_keys,
        )

    return observable_data_lake
