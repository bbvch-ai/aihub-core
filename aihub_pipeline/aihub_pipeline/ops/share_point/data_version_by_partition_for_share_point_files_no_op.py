from typing import List

from dagster import (
    AssetKey,
    AssetMaterialization,
    DataVersionsByPartition,
    DynamicPartitionsDefinition,
    OpExecutionContext,
)

from aihub_pipeline.types.SharePointFile import MinimalSharePointFile
from aihub_pipeline.util.meta_utils import sharepoint_metadata_table
from aihub_pipeline.util.partition_utils import replace_partition_keys


def data_version_by_partition_for_share_point_files_no_op(
    context: OpExecutionContext,
    asset_key: AssetKey,
    partition: DynamicPartitionsDefinition,
    sharepoint_files: List[MinimalSharePointFile],
) -> DataVersionsByPartition:
    """Generates a dynamic partition key for each file in SharePoint, reports the SharePoint materialization
    and returns a DataVersion for each partition key.
    """
    context.log.info(f"Found {len(sharepoint_files)} files in SharePoint")
    replace_partition_keys(
        context,
        partition.name,
        [sharepoint_file.id for sharepoint_file in sharepoint_files],
    )

    if sharepoint_files:
        context.instance.report_runless_asset_event(
            AssetMaterialization(
                asset_key=asset_key,
                partition=sharepoint_files[-1].id,
                metadata={
                    "Number of Files": len(sharepoint_files),
                    "Total File Size (MB)": sum([sharepoint_file.size for sharepoint_file in sharepoint_files]) / 1e6,
                    "Table": sharepoint_metadata_table(sharepoint_files),
                },
            )
        )

    # Using both etag and modified timestamp provides robust change detection:
    # - etag changes on any file modification (content or metadata)
    # - modified timestamp provides additional temporal context
    return DataVersionsByPartition(
        {
            sharepoint_file.id: f"{sharepoint_file.modified}-{sharepoint_file.etag}"
            for sharepoint_file in sharepoint_files
        }
    )
