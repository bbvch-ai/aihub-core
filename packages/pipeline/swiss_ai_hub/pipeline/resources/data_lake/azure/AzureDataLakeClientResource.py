from azure.storage.filedatalake import DataLakeServiceClient
from dagster import InitResourceContext
from swiss_ai_hub.core.infrastructure.azure_data_lake.AzureDataLakeSettings import AzureDataLakeSettings

from swiss_ai_hub.pipeline.resources.data_lake.azure.AzureDataLakeClient import AzureDataLakeClient
from swiss_ai_hub.pipeline.resources.data_lake.base.AbstractDataLakeClientResource import AbstractDataLakeClientResource


class AzureDataLakeClientResource(AbstractDataLakeClientResource[AzureDataLakeClient]):
    """
    A resource that provides a FileSystemClient for interacting with the Azure Data Lake using
    the Azure SDK for Python. The FileSystemClient is suitable when you need granular control over storage operations,
    such as setting specific permissions or metadata.

    You can use this client SDK when you want to get specific details of a file like its metadata, when it
    last changed, etc.

    You should not use this client SDK when you want to open the file and read its contents. For that, you should use
    the AzureBlobFileSystem provided by the AzureDataLakeFileSystemResource.

    **Note**: When using the client SDK, you have access to both your own namespace as well as all other namespaces
    in the organization. Be extra careful when using this client SDK.

    When using the client SDK in combination with the AzureBlobFileSystem, there is a quirk: The scope of the
    file system is the whole data lake, e.g. you see the different organizations as folders in the root directory.
    The namespaces are represented by subfolders in the respective organization folder.
    However, the client SDK only sees the organization folder as the root directory. This means that file paths
    received from the client SDK must first be translated to the organization folder before being used with the
    AzureBlobFileSystem, and vice versa, simply by adding or removing a path prefix corresponding to the organization
    name.

    Example usage:

    1. Directly interact with the azure data lake file system:

    .. code-block:: python

        from swiss_ai_hub.pipeline.resources.data_lake.azure.AzureDataLakeClientResource import AzureDataLakeClientResource

        from dagster import Definitions, asset

        @asset
        def asset1(namespace: NamespaceResource, data_lake_client: ResourceParam[FileSystemClient]):
            paths = data_lake_client.get_paths(path=f"{namespace.name}/", recursive=True)

        defs = Definitions(
            assets=[asset1],
            resources={
                "data_lake_client": AzureDataLakeClientResource(container_name="my_container")
            }
        )

    2. Use the data lake file system as part of a data lake io manager:

    .. code-block:: python

        from swiss_ai_hub.pipeline.io.AzureDataLakeIOManager import AzureDataLakeIOManager
        from swiss_ai_hub.pipeline.resources.data_lake.azure.AzureDataLakeClientResource import AzureDataLakeClientResource
        from swiss_ai_hub.pipeline.resources.data_lake.azure.AzureDataLakeFileSystemResource
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

        data_lake_client = AzureDataLakeClientResource(container_name="my_container")

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

    def create_resource(self, context: InitResourceContext) -> AzureDataLakeClient:
        conn_str = AzureDataLakeSettings().CONNECTION_STRING.get_secret_value()
        data_lake_client = DataLakeServiceClient.from_connection_string(conn_str=conn_str)
        filesystem_client = data_lake_client.get_file_system_client(file_system=self.container_name)
        return AzureDataLakeClient(self.container_name, filesystem_client)
