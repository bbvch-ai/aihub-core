from dagster import ConfigurableIOManager, InputContext, OutputContext, ResourceDependency

from aihub_pipeline.resources.rclone.RcloneResource import RcloneResource
from aihub_pipeline.types.RcloneFile import MinimalRcloneFile, RcloneFile


class RcloneIOManager(ConfigurableIOManager):
    """Rclone IO Manager for loading files from any rclone-supported backend.

    **Why this exists**: This IO Manager loads external files from 70+ cloud storage
    providers (OneDrive, SharePoint, S3, Azure, Google Drive, etc.) and returns domain
    objects (RcloneFile/MinimalRcloneFile).

    **Two loading patterns**:

    1. **Partitioned asset** (standard): Returns single ``RcloneFile`` with full content.
       Used for: Processing files individually (parsing, uploading, transformation).
       Enables parallel execution and incremental updates.

    2. **Non-partitioned asset** (cleanup only): Returns ``list[MinimalRcloneFile]`` with metadata only.
       Used for: Comparing all source files vs storage to find orphans for deletion.
       Why metadata-only: Cleanup only needs paths/timestamps, not content. Loading all file
       content would waste memory and time.

    **Usage**: Always use resource key ``"rclone_io_manager"``, never ``"io_manager"``.
    Requires RcloneResource dependency for file scanning and loading.

    Does not support writing outputs back to the remote.
    """

    rclone_client: ResourceDependency[RcloneResource]

    def handle_output(self, context: OutputContext, obj: bytes | RcloneFile):
        """
        Currently we do not support writing outputs to rclone remotes.
        Our pipelines should not require writing outputs back to source systems.
        """
        raise NotImplementedError("Writing outputs to rclone remotes is not supported.")

    def load_input(self, context: InputContext) -> RcloneFile | list[MinimalRcloneFile]:
        """
        Load rclone files based on the partition key or upstream output.

        CAREFUL: If no partition key is provided, it will fetch all
        files from the upstream output but WITHOUT downloading them.
        """
        if context.has_partition_key:
            return self.rclone_client.download_file(context.partition_key)
        else:
            upstream_output = context.upstream_output
            partitions_def = upstream_output.asset_partitions_def

            if partitions_def is not None:
                all_partition_keys = partitions_def.get_partition_keys(dynamic_partitions_store=context.instance)
                # Return minimal files (metadata only) for all partitions
                # This is used for cleanup operations comparing source vs data lake
                all_files = self.rclone_client.fetch_minimal_files()
                # Filter to only partitions that exist
                partition_set = set(all_partition_keys)
                return [f for f in all_files if f.path in partition_set]
            else:
                context.log.error("No partition definition found for the upstream asset.")
                raise ValueError("No partition keys found in upstream output")
