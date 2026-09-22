from dagster import ConfigurableIOManager, InputContext, OutputContext

from swiss_ai_hub.pipeline.types.rclone_file import MinimalRcloneFile, RcloneFile
from swiss_ai_hub.pipeline.util.async_utils import run_async
from swiss_ai_hub.pipeline.util.partition_utils import split_composite_partition_key
from swiss_ai_hub.pipeline.util.run_routing import bucket_from_run_tag
from swiss_ai_hub.pipeline.util.source_builders import build_rclone_client, rclone_remote_for_bucket


class RoutedRcloneIOManager(ConfigurableIOManager):
    """
    Read-only access to every database's rclone remote, routed per run by bucket.

    The rclone source pipeline shares one partition registry across every knowledge database, so partition keys
    are composite ``{bucket}|{remote path}``. On the partitioned read the bucket comes from the key and the file
    is downloaded from that database's remote. On the non-partitioned read (the removal asset) the bucket comes
    from the ``aihub/bucket`` run tag and only metadata is listed, filtered to the keys that database currently
    has — comparing source and data lake needs paths, not content.
    """

    source: str

    def handle_output(self, context: OutputContext, obj: object) -> None:
        raise NotImplementedError("RoutedRcloneIOManager is read-only; sources are never written to.")

    def load_input(self, context: InputContext) -> RcloneFile | list[MinimalRcloneFile]:
        if context.has_partition_key:
            bucket, path = split_composite_partition_key(context.partition_key)
            remote = rclone_remote_for_bucket(bucket, self.source)
            return run_async(build_rclone_client().download_bytes(remote.fs, path))

        bucket = bucket_from_run_tag(context)
        partitions_def = context.upstream_output.asset_partitions_def
        if partitions_def is None:
            raise ValueError("Cannot load source files without partition information.")

        bucket_prefix = f"{bucket}|"
        known_paths = {
            split_composite_partition_key(key)[1]
            for key in partitions_def.get_partition_keys(dynamic_partitions_store=context.instance)
            if key.startswith(bucket_prefix)
        }
        remote = rclone_remote_for_bucket(bucket, self.source)
        files = run_async(
            build_rclone_client().list_files(
                remote.fs, include=remote.include_patterns, exclude=remote.exclude_patterns
            )
        )
        return [file for file in files if file.path in known_paths]
