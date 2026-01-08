from adlfs import AzureBlobFileSystem
from aihub_lib.infrastructure.azure_data_lake.AzureDataLakeSettings import AzureDataLakeSettings
from dagster import InitResourceContext

from aihub_pipeline.resources.data_lake.base.AbstractDataLakeFileSystemResource import (
    AbstractDataLakeFileSystemResource,
)


class AzureDataLakeFileSystemResource(AbstractDataLakeFileSystemResource[AzureBlobFileSystem]):
    """
    This resource gives access to the Azure Blob File System and hence lets you interact
    with files on azure data lake as if they were on a local file system.

    This way, we can leverage any library that wants to read/write file from/to the file system
    by just passing the azure data lake file system as a regular fs object.

    You can either use this resource stand-alone or as part of a data lake IO manager.

    **Note**: When you directly engage with the file system, you need to be extra careful you will have access
    to both the files in your organization as well as files in all other organization, and even files that
    dagster writes as part of operation inputs/outputs! If you just want to load assets from or
    write assets to the data lake, it is safer to use the data lake io manager!

    Example usage:

    1. Directly interact with the azure data lake file system:

    .. code-block:: python
        from aihub_pipeline.resources.data_lake.azure.AzureDataLakeFileSystemResource
        import AzureDataLakeFileSystemResource

        from dagster import Definitions, asset

        @asset
        def asset1(data_lake_file_system: ResourceParam[AbstractFileSystem]):
            with data_lake_file_system.open("path/to/file") as f:
                return f.read()

        defs = Definitions(
            assets=[asset1],
            resources={
                "data_lake_file_system": AzureDataLakeFileSystemResource()}
        )

    2. Use the data lake file system as part of a data lake io manager:

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

    def create_resource(self, context: InitResourceContext) -> AzureBlobFileSystem:
        conn_str = AzureDataLakeSettings().CONNECTION_STRING.get_secret_value()
        return AzureBlobFileSystem(
            connection_string=conn_str,
            connection_timeout=30,  # 30 seconds for connection establishment
            read_timeout=300,  # 5 minutes for read operations
        )
