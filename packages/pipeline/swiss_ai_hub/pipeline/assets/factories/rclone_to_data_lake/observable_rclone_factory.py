from dagster import (
    AssetKey,
    DataVersionsByPartition,
    DynamicPartitionsDefinition,
    OpExecutionContext,
    observable_source_asset,
)

from swiss_ai_hub.pipeline.ops.rclone.data_version_by_partition_for_rclone_files import (
    data_version_by_partition_for_rclone_files,
)
from swiss_ai_hub.pipeline.resources.rclone.RcloneResource import RcloneResource
from swiss_ai_hub.pipeline.util.key_utils import group_name_from_asset_key


def observable_rclone_factory(
    key: AssetKey,
    partitions: DynamicPartitionsDefinition,
    max_partitions: int,
    encode_partition_keys: bool = False,
) -> observable_source_asset:
    """
    Observable source asset for cloud storage (OneDrive, Dropbox, Google Drive, etc.).

    **Why hash-based change detection**: Detects ANY content change with zero false positives.
    Prefers MD5/SHA1 from backend, falls back to mtime+size if hash unavailable.

    **Why rclone**: Single implementation for 70+ providers without provider-specific SDKs.
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
            max_partitions=max_partitions,
            encode_partition_keys=encode_partition_keys,
        )

    return observable_rclone
