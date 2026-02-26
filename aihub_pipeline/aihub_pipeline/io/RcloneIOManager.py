from aihub_lib.generative_ai.utils.path_utils import decode_partition_key
from dagster import ConfigurableIOManager, InputContext, OutputContext, ResourceDependency

from aihub_pipeline.resources.rclone.RcloneResource import RcloneResource
from aihub_pipeline.types.RcloneFile import MinimalRcloneFile, RcloneFile


class RcloneIOManager(ConfigurableIOManager):
    """
    Load files from cloud storage via rclone (OneDrive, Dropbox, Google Drive, etc.).

    **Why two loading patterns**:
    - Partitioned: Returns RcloneFile with content (for processing)
    - Non-partitioned: Returns MinimalRcloneFile list (metadata only, for cleanup comparison)

    **Why metadata-only for cleanup**: Comparing source vs data lake only needs paths/timestamps,
    not file content. Loading all content would waste memory and time.

    **Why read-only**: RAG pipelines never write back to source systems.
    """

    rclone_client: ResourceDependency[RcloneResource]
    encode_partition_keys: bool = False

    def handle_output(self, context: OutputContext, obj: bytes | RcloneFile):
        raise NotImplementedError("Writing to rclone remotes not supported (read-only)")

    def load_input(self, context: InputContext) -> RcloneFile | list[MinimalRcloneFile]:
        if context.has_partition_key:
            if self.encode_partition_keys:
                path = decode_partition_key(context.partition_key)
            else:
                path = context.partition_key
            return self.rclone_client.download_file(path)

        upstream_output = context.upstream_output
        partitions_def = upstream_output.asset_partitions_def

        if partitions_def is None:
            raise ValueError("No partition definition found")

        all_partition_keys = partitions_def.get_partition_keys(dynamic_partitions_store=context.instance)
        all_files = self.rclone_client.fetch_minimal_files()

        if self.encode_partition_keys:
            known_paths = {decode_partition_key(k) for k in all_partition_keys}
        else:
            known_paths = set(all_partition_keys)
        return [f for f in all_files if f.path in known_paths]
