from adlfs import AzureBlobFileSystem
from dagster import ConfigurableResource, InitResourceContext
from lib_core.infrastructure.azure.data_lake import DataLakeAccess


class DataLakeFileSystemResource(ConfigurableResource[AzureBlobFileSystem]):
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
        from pipelines_core.resources.data_lake.DataLakeFileSystemResource import DataLakeFileSystemResource

        from dagster import Definitions, asset

        @asset
        def asset1(data_lake_file_system: ResourceParam[AbstractFileSystem]):
            with data_lake_file_system.open("path/to/file") as f:
                return f.read()

        defs = Definitions(
            assets=[asset1],
            resources={
                "data_lake_file_system": DataLakeFileSystemResource()}
        )

    2. Use the data lake file system as part of a data lake io manager:

    .. code-block:: python

        from pipelines_core.io.AzureDataLakeIOManager import AzureDataLakeIOManager
        from pipelines_core.resources.data_lake.DataLakeClientResource import DataLakeClientResource
        from pipelines_core.resources.data_lake.DataLakeFileSystemResource import DataLakeFileSystemResource
        from pipelines_core.resources.organization.NamespaceResource import NamespaceResource

        from dagster import Definitions, asset

        @asset(partitions_def=my_partition, "io_manager_key=data_lake_io_manager")
        def create_file_on_lake(namespace: NamespaceResource) -> DataLakeFile:
            # Manually create a file to be written to data lake
            uri = f"/{namespace.organization}/{namespace.name}/my_file.txt"
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

        namespace = NamespaceResource(name="my_namespace", organization="my_organization")
        data_lake_client = DataLakeClientResource(
            namespace=namespace,
        )
        data_lake_file_system = DataLakeFileSystemResource()
        data_lake_io_manager = AzureDataLakeIOManager(
            data_lake_client=data_lake_client,
            data_lake_file_system=data_lake_file_system,
        )

        defs = Definitions(
            assets=[create_file_on_lake, downstream_asset],
            resources={
                "namespace": namespace,
                "data_lake_client": data_lake_client,
                "data_lake_file_system": data_lake_file_system,
                "data_lake_io_manager": data_lake_io_manager,
            },
        )

    """

    def create_resource(self, context: InitResourceContext) -> AzureBlobFileSystem:
        return DataLakeAccess().get_fs_client()
