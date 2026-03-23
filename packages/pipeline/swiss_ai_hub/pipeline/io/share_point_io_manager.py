import asyncio

from dagster import ConfigurableIOManager, InputContext, OutputContext, ResourceDependency

from swiss_ai_hub.pipeline.resources.share_point.share_point_resource import SharePointResource
from swiss_ai_hub.pipeline.types.share_point_file import MinimalSharePointFile, SharePointFile


class SharePointIoManager(ConfigurableIOManager):
    share_point_client: ResourceDependency[SharePointResource]

    def handle_output(self, context: OutputContext, obj: bytes | SharePointFile):
        """
        Currently we do not support writing outputs to SharePoint.
        We do not have access to any SharePoint API that allows writing files.
        Our pipelines should not require writing outputs to SharePoint.
        """
        raise NotImplementedError("Writing outputs to SharePoint is not supported.")

    def load_input(self, context: InputContext) -> SharePointFile | list[MinimalSharePointFile]:
        """
        Load SharePoint files based on the partition key or upstream output.
        CAREFUL: If no partition key is provided, it will fetch all
        files from the upstream output but WITHOUT downloading them.
        """
        if context.has_partition_key:
            return self.share_point_client.download_file(context.partition_key)
        else:
            upstream_output = context.upstream_output
            partitions_def = upstream_output.asset_partitions_def

            if partitions_def is not None:
                all_partition_keys = partitions_def.get_partition_keys(dynamic_partitions_store=context.instance)
                return asyncio.run(
                    self.share_point_client.get_multiple_minimal_share_point_files(list(all_partition_keys))
                )
            else:
                context.log.error("No partition definition found for the upstream asset.")
                raise ValueError("No partition keys found in upstream output")
