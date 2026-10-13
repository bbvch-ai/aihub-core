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
from swiss_ai_hub.pipeline.util.async_utils import run_async
from swiss_ai_hub.pipeline.util.key_utils import group_name_from_asset_key
from swiss_ai_hub.pipeline.util.run_routing import bucket_from_run_tag
from swiss_ai_hub.pipeline.util.source_builders import build_rclone_client, rclone_remote_for_bucket


def observable_rclone_factory(
    key: AssetKey,
    partitions: DynamicPartitionsDefinition,
    *,
    source: str,
    max_partitions: int,
) -> observable_source_asset:
    """Observes one knowledge database's rclone remote, resolved from the run.

    The bucket travels in the ``aihub/bucket`` run tag; its remote is rebuilt from the stored source configuration
    on every observation, so credential edits and a restarted daemon need no operator action.
    """

    @observable_source_asset(
        key=key,
        group_name=group_name_from_asset_key(key),
        partitions_def=partitions,
        io_manager_key="rclone_io_manager",
        description="Observes the remote of the knowledge database this run targets (routed by run tag)",
    )
    def observable_rclone(context: OpExecutionContext) -> DataVersionsByPartition:
        bucket = bucket_from_run_tag(context)
        remote = rclone_remote_for_bucket(bucket, source)
        files = run_async(
            build_rclone_client().list_files(
                remote.fs, include=remote.include_patterns, exclude=remote.exclude_patterns
            )
        )
        return data_version_by_partition_for_rclone_files(
            context=context,
            asset_key=key,
            partition=partitions,
            bucket=bucket,
            rclone_files=files,
            max_partitions=max_partitions,
        )

    return observable_rclone
