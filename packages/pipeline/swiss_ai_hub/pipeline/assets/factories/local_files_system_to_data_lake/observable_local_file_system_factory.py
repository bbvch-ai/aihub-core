from dagster import (
    AssetKey,
    DataVersionsByPartition,
    DynamicPartitionsDefinition,
    OpExecutionContext,
    observable_source_asset,
)

from swiss_ai_hub.pipeline.ops.local_file_system.data_version_by_partition_for_local_files import (
    data_version_by_partition_for_local_files,
)
from swiss_ai_hub.pipeline.resources.local_file_system.LocalFileSystemResource import LocalFileSystemResource
from swiss_ai_hub.pipeline.util.key_utils import group_name_from_asset_key


def observable_local_file_system_factory(
    key: AssetKey,
    partitions: DynamicPartitionsDefinition,
    max_partitions: int,
    encode_partition_keys: bool = False,
) -> observable_source_asset:
    """
    Factory to create an observable source asset for local filesystem monitoring.

    This asset scans the configured customer folders and creates dynamic partitions
    for each file, using mtime + size as the data version to detect changes.
    """

    @observable_source_asset(
        key=key,
        group_name=group_name_from_asset_key(key),
        partitions_def=partitions,
        io_manager_key="local_file_system_io_manager",
        description="Observes the local filesystem for customer files and detects changes",
    )
    def observable_local_file_system(
        context: OpExecutionContext,
        local_file_system_client: LocalFileSystemResource,
    ) -> DataVersionsByPartition:
        local_files = local_file_system_client.fetch_all_files()

        return data_version_by_partition_for_local_files(
            context=context,
            asset_key=key,
            partition=partitions,
            local_files=local_files,
            max_partitions=max_partitions,
            encode_partition_keys=encode_partition_keys,
        )

    return observable_local_file_system
