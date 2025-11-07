import asyncio

from dagster import ConfigurableIOManager, InputContext, OutputContext, ResourceDependency

from aihub_pipeline.resources.local_file_system.LocalFileSystemResource import LocalFileSystemResource
from aihub_pipeline.types.LocalFile import LocalFile, MinimalLocalFile


class LocalFileSystemIOManager(ConfigurableIOManager):
    local_file_system_client: ResourceDependency[LocalFileSystemResource]

    def handle_output(self, context: OutputContext, obj: bytes | LocalFile):
        """
        Currently we do not support writing outputs to the local file system.
        """
        raise NotImplementedError("Writing outputs to the local file system is not supported.")

    def load_input(self, context: InputContext) -> LocalFile | list[MinimalLocalFile]:
        if context.has_partition_key:
            return self.local_file_system_client.get_local_file(context.partition_key)
        else:
            upstream_output = context.upstream_output
            partitions_def = upstream_output.asset_partitions_def

            if partitions_def is not None:
                all_partition_keys = partitions_def.get_partition_keys(dynamic_partitions_store=context.instance)
                return asyncio.run(self.local_file_system_client.get_minimal_local_files(list(all_partition_keys)))
            else:
                context.log.error("No partition definition found for the upstream asset.")
                raise ValueError("No partition keys found in upstream output")
