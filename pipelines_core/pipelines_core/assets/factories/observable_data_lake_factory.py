from typing import List

from azure.storage.filedatalake import FileSystemClient
from dagster import (
    AssetKey,
    DataVersionsByPartition,
    DynamicPartitionsDefinition,
    OpExecutionContext,
    ResourceParam,
    observable_source_asset,
)

from pipelines_core.ops.data_lake.data_version_by_partition_for_data_lake_files import (
    data_version_by_partition_for_data_lake_files_no_op,
)
from pipelines_core.ops.data_lake.fetch_all_files_in_data_lake import (
    fetch_all_files_in_data_lake_no_op,
)
from pipelines_core.resources.organization.NamespaceResource import NamespaceResource
from pipelines_core.types.DataLakeFile import DataLakeFile
from pipelines_core.util.key_utils import group_name_from_asset_key


def observable_data_lake_factory(
    key: AssetKey, partitions: DynamicPartitionsDefinition
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
        data_lake_client: ResourceParam[FileSystemClient],
        namespace: NamespaceResource,
    ) -> DataVersionsByPartition:
        data_lake_files: List[DataLakeFile] = fetch_all_files_in_data_lake_no_op(
            context=context,
            data_lake_client=data_lake_client,
            namespace=namespace,
        )
        return data_version_by_partition_for_data_lake_files_no_op(
            context=context,
            asset_key=key,
            namespace=namespace,
            partition=partitions,
            data_lake_files=data_lake_files,
        )

    return observable_data_lake
