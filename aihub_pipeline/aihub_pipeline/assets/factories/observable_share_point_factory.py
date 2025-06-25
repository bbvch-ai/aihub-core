from typing import List

from dagster import (
    AssetKey,
    DataVersionsByPartition,
    DynamicPartitionsDefinition,
    OpExecutionContext,
    ResourceParam,
    observable_source_asset,
)

from aihub_pipeline.ops.sharepoint.data_version_by_partition_for_share_point_files_no_op import (
    data_version_by_partition_for_share_point_files_no_op,
)
from aihub_pipeline.resources.share_point.SharePointResource import SharePointResource
from aihub_pipeline.types.SharePointFile import MinimalSharePointFile
from aihub_pipeline.util.key_utils import group_name_from_asset_key


def observable_share_point_factory(key: AssetKey, partitions: DynamicPartitionsDefinition) -> observable_source_asset:
    """Creates an observable source asset representing a sharepoint site containing files that should be processed
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
    def observable_share_point(
        context: OpExecutionContext,
        sharepoint_client: ResourceParam[SharePointResource],
    ) -> DataVersionsByPartition:
        share_point_files: List[MinimalSharePointFile] = sharepoint_client.fetch_minimal_files()
        return data_version_by_partition_for_share_point_files_no_op(
            context=context,
            partition=partitions,
            sharepoint_files=share_point_files,
            asset_key=key,
        )

    return observable_share_point
