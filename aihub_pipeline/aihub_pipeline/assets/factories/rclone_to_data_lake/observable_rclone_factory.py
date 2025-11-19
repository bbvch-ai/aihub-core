from dagster import (
    AssetKey,
    DataVersionsByPartition,
    DynamicPartitionsDefinition,
    OpExecutionContext,
    observable_source_asset,
)

from aihub_pipeline.ops.rclone.data_version_by_partition_for_rclone_files import (
    data_version_by_partition_for_rclone_files,
)
from aihub_pipeline.resources.rclone.RcloneResource import RcloneResource
from aihub_pipeline.util.key_utils import group_name_from_asset_key


def observable_rclone_factory(
    key: AssetKey,
    partitions: DynamicPartitionsDefinition,
) -> observable_source_asset:
    """
    Factory to create an observable source asset for any rclone-supported backend.

    This asset scans the configured rclone remote (OneDrive, SharePoint, S3, Azure,
    Google Drive, Dropbox, local filesystem, etc.) and creates dynamic partitions
    for each file, using mtime + size as the data version to detect changes.

    **Why rclone**: Single implementation works across 70+ cloud storage providers
    without provider-specific code or SDKs.

    **Usage**: Configure RcloneResource with source_remote and filters, then use this
    factory to create an observable asset that monitors the remote for changes.
    """

    @observable_source_asset(
        key=key,
        group_name=group_name_from_asset_key(key),
        partitions_def=partitions,
        io_manager_key="rclone_io_manager",
        description="Observes rclone remote for files and detects changes",
    )
    def observable_rclone(
        context: OpExecutionContext,
        rclone_client: RcloneResource,
    ) -> DataVersionsByPartition:
        rclone_files = rclone_client.fetch_minimal_files()

        return data_version_by_partition_for_rclone_files(
            context=context,
            asset_key=key,
            partition=partitions,
            rclone_files=rclone_files,
        )

    return observable_rclone
