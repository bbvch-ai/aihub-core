from dagster import (
    AssetKey,
    AssetMaterialization,
    DataVersionsByPartition,
    DynamicPartitionsDefinition,
    OpExecutionContext,
)

from swiss_ai_hub.pipeline.types.share_point_file import MinimalSharePointFile
from swiss_ai_hub.pipeline.util.meta_utils import share_point_metadata_table
from swiss_ai_hub.pipeline.util.partition_utils import replace_partition_keys


def data_version_by_partition_for_share_point_files_no_op(
    context: OpExecutionContext,
    asset_key: AssetKey,
    partition: DynamicPartitionsDefinition,
    share_point_files: list[MinimalSharePointFile],
    max_partitions: int,
) -> DataVersionsByPartition:
    """Generates a dynamic partition key for each file in SharePoint, reports the SharePoint materialization
    and returns a DataVersion for each partition key.
    """
    context.log.info(f"Found {len(share_point_files)} files in SharePoint")
    replace_partition_keys(
        context,
        partition.name,
        [share_point_file.id for share_point_file in share_point_files],
        max_partitions,
    )

    if share_point_files:
        context.instance.report_runless_asset_event(
            AssetMaterialization(
                asset_key=asset_key,
                partition=share_point_files[-1].id,
                metadata={
                    "Number of Files": len(share_point_files),
                    "Total File Size (MB)": sum([share_point_file.size for share_point_file in share_point_files])
                    / 1e6,
                    "Table": share_point_metadata_table(share_point_files),
                },
            )
        )

    # Using both etag and modified timestamp provides robust change detection:
    # - etag changes on any file modification (content or metadata)
    # - modified timestamp provides additional temporal context

    existing_partitions = set(context.instance.get_dynamic_partitions(partition.name))
    files_with_partitions = [
        share_point_file for share_point_file in share_point_files if share_point_file.id in existing_partitions
    ]

    return DataVersionsByPartition(
        {
            share_point_file.id: f"{share_point_file.modified}-{share_point_file.etag}"
            for share_point_file in files_with_partitions
        }
    )
