import base64
from urllib.parse import quote, unquote

from adlfs import AzureBlobFileSystem
from azure.storage.filedatalake import ContentSettings
from dagster import ConfigurableIOManager, InputContext, OutputContext, ResourceDependency

from aihub_pipeline.resources.data_lake.azure.AzureDataLakeClient import AzureDataLakeClient
from aihub_pipeline.types.DataLakeFile import DataLakeFile


class AzureDataLakeIOManager(ConfigurableIOManager):
    """Azure Data Lake IO Manager for loading and storing files from/to the Azure Data Lake.

    This IO Manager is different from the dagster default ADLS2PickleIOManager in its intended use.
    Use the ADLS2PickleIOManager from dagster to store ops outputs as pickles to a distinct folder
    in the data lake that is only used by dagster. It holds in-between artifacts that are required
    to coordinate the individual pipeline-steps.

    Use this AzureDataLakeIOManager IO Manager to load and store user files from/to the Azure Data Lake
    that should be forwarded through the pipelines. These objects are not pickles but rather raw files
    that will later be processed by our own data loaders. This IO Manager is aware of the metadata
    added to data lake files and always returns a DataLakeFile object, not pickled data.

    The AzureDataLakeIOManager depends on two other resources:
    - **AzureDataLakeClientResource**: Responsible for providing the FileSystemClient to
      interact with the Azure Data Lake.
    - **AzureDataLakeFileSystemResource**: Responsible for providing the AzureBlobFileSystem to interact with the
    Azure Data Lake.

    Hence, do NOT use this IO Manager as the default io_manager with the resource key ``"io_manager"``.
    In most cases, you'll want to use it with the resource key ``"data_lake_io_manager"``.

    This IO Manager assumes data partitioning. It can handle two cases:
    - **partitioned asset**: The IO Manager wraps an asset that is partitioned. In this case, the IO Manager
    will load the data lake file corresponding to the partition key.
    - **non-partitioned asset**: The IO Manager wraps an asset that is not partitioned. In this case, the IO Manager
    assumes that the upstream asset was partitioned and will load all data lake files corresponding to all
    partition keys available to the upstream dependency.

    **Note**: The IO Manager currently does not handle the case in which the pipeline is not partitioned
    and only handles a single file.

    Example usage:

    1. Attach an IO manager to a set of assets using the resource key ``"data_lake_io_manager"``

    .. code-block:: python

        from aihub_pipeline.io.AzureDataLakeIOManager import AzureDataLakeIOManager
        from aihub_pipeline.resources.data_lake.azure.AzureDataLakeClientResource import AzureDataLakeClientResource
        from aihub_pipeline.resources.data_lake.azure.AzureDataLakeFileSystemResource
        import AzureDataLakeFileSystemResource

        from dagster import Definitions, asset

        @asset(partitions_def=my_partition, "io_manager_key=data_lake_io_manager")
          def create_file_on_lake(container_name, directory_name) -> DataLakeFile:
            # Manually create a file to be written to data lake
            uri = f"/{container_name}/{directory_name}/my_file.txt"
            content = b"Hello, Azure Data Lake!"
            metadata = {"author": "John Doe"}
            return DataLakeFile.from_content(
                uri=uri,
                content=content,
                metadata=metadata,
            )



        @asset(partitions_def=my_partition)
        def downstream_asset(create_file_on_lake: DataLakeFile):
            # The input asset will be loaded from the data_lake
            ...

        data_lake_client = AzureDataLakeClientResource(
            container_name="my_container",
        )
        data_lake_file_system = AzureDataLakeFileSystemResource()
        data_lake_io_manager = AzureDataLakeIOManager(
            data_lake_client=data_lake_client,
            data_lake_file_system=data_lake_file_system,
        )

        defs = Definitions(
            assets=[create_file_on_lake, downstream_asset],
            resources={
                "data_lake_client": data_lake_client,
                "data_lake_file_system": data_lake_file_system,
                "data_lake_io_manager": data_lake_io_manager,
            },
        )
    """

    data_lake_client: ResourceDependency[AzureDataLakeClient]
    data_lake_file_system: ResourceDependency[AzureBlobFileSystem]

    def handle_output(self, context: OutputContext, obj: DataLakeFile | list[DataLakeFile]) -> None:
        if isinstance(obj, DataLakeFile):
            data_lake_files = [obj]
        elif isinstance(obj, list) and all(isinstance(item, DataLakeFile) for item in obj):
            data_lake_files = obj
        else:
            context.log.error("Output is neither a DataLakeFile nor a list of DataLakeFiles.")
            raise ValueError("Expected a DataLakeFile or a list of DataLakeFiles.")

        for data_lake_file in data_lake_files:
            if data_lake_file.content is None:
                context.log.error(f"No content found for file {data_lake_file.uri}. Cannot write to data lake.")
                raise ValueError(f"No content to write for file {data_lake_file.uri}.")

            # Use the data_lake_file_system to write the content to the specified path
            file_path = data_lake_file.uri.lstrip("/")  # Remove leading slash if present
            context.log.info(f"Writing file to data lake at path: {file_path}")

            # Write the content to the data lake
            with self.data_lake_file_system.open(file_path, mode="wb") as f:
                f.write(data_lake_file.content)

            # Encode metadata before setting it on the file
            encoded_metadata = self._encode_metadata(data_lake_file.metadata)

            file_path_without_org = file_path.split("/", 1)[1]  # Remove the organization from the path
            file_client = self.data_lake_client.raw_client.get_file_client(file_path_without_org)
            file_client.set_metadata(encoded_metadata)

            content_settings = ContentSettings(
                content_type=data_lake_file.content_type,
                content_md5=base64.b64decode(data_lake_file.hash),
            )
            file_client.set_http_headers(content_settings=content_settings)

            context.log.info(f"Successfully wrote file {data_lake_file.uri} to data lake.")

    def load_input(self, context: InputContext) -> DataLakeFile | list[DataLakeFile]:
        if context.has_partition_key:
            # If the context has a partition key, proceed as usual
            document_uri = context.partition_key
            context.log.info(f"Loading DataLakeFile from uri: {document_uri}")
            data_lake_file = self.data_lake_client.create_data_lake_file_from_uri(document_uri)

            # Decode metadata after retrieval
            decoded_metadata = self._decode_metadata(data_lake_file.metadata)
            data_lake_file.metadata = decoded_metadata

            return data_lake_file
        else:
            # No partition key, load all partitions
            upstream_output = context.upstream_output
            partitions_def = upstream_output.asset_partitions_def

            if partitions_def is not None:
                # Pass the instance's dynamic partitions store
                all_partition_keys = partitions_def.get_partition_keys(dynamic_partitions_store=context.instance)
                data_lake_files = []
                for partition_key in all_partition_keys:
                    document_uri = partition_key
                    context.log.info(f"Loading DataLakeFile from uri: {document_uri}")
                    data_lake_file = self.data_lake_client.create_data_lake_file_from_uri(document_uri)

                    # Decode metadata after retrieval
                    decoded_metadata = self._decode_metadata(data_lake_file.metadata)
                    data_lake_file.metadata = decoded_metadata

                    data_lake_files.append(data_lake_file)
                return data_lake_files  # Return the list or process it as needed
            else:
                context.log.error("No partition definition found for the upstream asset.")
                raise ValueError("Cannot load data without partition information.")

    @staticmethod
    def _encode_metadata(metadata: dict) -> dict:
        return {quote(key, safe=""): quote(str(value), safe=":/?&=") for key, value in metadata.items()}

    @staticmethod
    def _decode_metadata(metadata: dict) -> dict:
        return {unquote(key): unquote(value) for key, value in metadata.items()}
