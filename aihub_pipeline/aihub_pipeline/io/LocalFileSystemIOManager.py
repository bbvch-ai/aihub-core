from aihub_lib.generative_ai.utils.path_utils import decode_partition_key
from dagster import ConfigurableIOManager, InputContext, OutputContext, ResourceDependency

from aihub_pipeline.resources.local_file_system.LocalFileSystemResource import LocalFileSystemResource
from aihub_pipeline.types.SourceFile import MinimalSourceFile, SourceFile


class LocalFileSystemIOManager(ConfigurableIOManager):
    """Local File System IO Manager for loading files from local or network file systems.

    **Why this exists**: This IO Manager loads external user files from the filesystem and returns domain objects
    (SourceFile/MinimalSourceFile).

    **Two loading patterns**:

    1. **Partitioned asset** (standard): Returns single ``SourceFile`` with full content.
       Used for: Processing files individually (parsing, uploading, transformation).
       Enables parallel execution and incremental updates.
       When ``encode_partition_keys`` is True, the partition key is URL-encoded;
       decoding recovers the exact original path.

    2. **Non-partitioned asset** (cleanup only): Returns ``list[MinimalSourceFile]`` with metadata only.
       Used for: Comparing all source files vs storage to find orphans for deletion.
       Why metadata-only: Cleanup only needs paths/timestamps, not content. Loading all file
       content would waste memory and time.

    **Usage**: Always use resource key ``"local_file_system_io_manager"``, never ``"io_manager"``.
    Requires LocalFileSystemResource dependency for file scanning and loading.

    Does not support writing outputs back to the file system.
    """

    local_file_system_client: ResourceDependency[LocalFileSystemResource]
    encode_partition_keys: bool = False

    def handle_output(self, context: OutputContext, obj: bytes | SourceFile):
        """
        Currently we do not support writing outputs to the local file system.
        """
        raise NotImplementedError("Writing outputs to the local file system is not supported.")

    def load_input(self, context: InputContext) -> SourceFile | list[MinimalSourceFile]:
        if context.has_partition_key:
            if self.encode_partition_keys:
                path = decode_partition_key(context.partition_key)
            else:
                path = context.partition_key
            return self.local_file_system_client.get_local_file(path)

        upstream_output = context.upstream_output
        partitions_def = upstream_output.asset_partitions_def

        if partitions_def is None:
            raise ValueError("No partition definition found for the upstream asset")

        all_partition_keys = partitions_def.get_partition_keys(dynamic_partitions_store=context.instance)
        if self.encode_partition_keys:
            all_partition_keys = [decode_partition_key(k) for k in all_partition_keys]
        return self.local_file_system_client.get_minimal_local_files(list(all_partition_keys))
