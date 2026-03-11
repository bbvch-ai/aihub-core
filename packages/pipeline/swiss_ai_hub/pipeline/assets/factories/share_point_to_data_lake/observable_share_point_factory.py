from dagster import (
    AssetKey,
    DataVersionsByPartition,
    DynamicPartitionsDefinition,
    OpExecutionContext,
    ResourceParam,
    observable_source_asset,
)

from swiss_ai_hub.pipeline.ops.share_point.data_version_by_partition_for_share_point_files_no_op import (
    data_version_by_partition_for_share_point_files_no_op,
)
from swiss_ai_hub.pipeline.resources.share_point.share_point_resource import SharePointResource
from swiss_ai_hub.pipeline.types.share_point_file import MinimalSharePointFile
from swiss_ai_hub.pipeline.util.key_utils import group_name_from_asset_key


def observable_share_point_factory(
    key: AssetKey,
    partitions: DynamicPartitionsDefinition,
    max_partitions: int,
) -> observable_source_asset:
    """
    Creates an observable source asset representing a sharepoint site containing files that should be processed
    by the pipeline. The asset generates a partition for each file in SharePoint as well as a DataVersion
    key based on the file content (etag and last modified date).
    """

    @observable_source_asset(
        key=key,
        group_name=group_name_from_asset_key(key),
        partitions_def=partitions,
        io_manager_key="sharepoint_io_manager",
        description="Observes the SharePoint site for any changes with respect to the DataLake.",
    )
    def observable_share_point(
        context: OpExecutionContext,
        share_point_client: ResourceParam[SharePointResource],
    ) -> DataVersionsByPartition:
        share_point_files: list[MinimalSharePointFile] = share_point_client.fetch_minimal_files()
        return data_version_by_partition_for_share_point_files_no_op(
            context=context,
            partition=partitions,
            share_point_files=share_point_files,
            asset_key=key,
            max_partitions=max_partitions,
        )

    return observable_share_point
