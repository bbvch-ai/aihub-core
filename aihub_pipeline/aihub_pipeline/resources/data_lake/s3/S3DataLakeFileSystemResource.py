import s3fs
from aihub_lib.infrastructure.s3.S3StorageSettings import S3StorageSettings
from dagster import InitResourceContext

from aihub_pipeline.resources.data_lake.base.AbstractDataLakeFileSystemResource import (
    AbstractDataLakeFileSystemResource,
)


class S3DataLakeFileSystemResource(AbstractDataLakeFileSystemResource[s3fs.S3FileSystem]):
    """
    This resource gives access to the S3-compatible File System (MinIO) and hence lets you interact
    with files on the data lake as if they were on a local file system.

    This way, we can leverage any library that wants to read/write file from/to the file system
    by just passing the S3 file system as a regular fs object.

    You can either use this resource stand-alone or as part of a data lake IO manager.

    **Note**: When you directly engage with the file system, you need to be extra careful about
    permissions and bucket access. If you just want to load assets from or
    write assets to S3, it is safer to use the data lake io manager!

    Example usage:

    1. Directly interact with the S3 file system:

    .. code-block:: python
        from aihub_pipeline.resources.data_lake.s3.S3DataLakeFileSystemResource import S3DataLakeFileSystemResource

        from dagster import Definitions, asset

        @asset
        def asset1(data_lake_file_system: ResourceParam[AbstractFileSystem]):
            with data_lake_file_system.open("s3://bucket-name/path/to/file") as f:
                return f.read()

        defs = Definitions(
            assets=[asset1],
            resources={
                "data_lake_file_system": S3DataLakeFileSystemResource()}
        )

    2. Use the data lake file system as part of a data lake io manager:

    .. code-block:: python

        from aihub_pipeline.io.S3DataLakeIOManager import S3DataLakeIOManager
        from aihub_pipeline.resources.data_lake.s3.S3DataLakeClientResource import S3DataLakeClientResource
        from aihub_pipeline.resources.data_lake.s3.S3DataLakeFileSystemResource import S3DataLakeFileSystemResource

        from dagster import Definitions, asset

        @asset(partitions_def=my_partition, "io_manager_key=data_lake_io_manager")
        def create_file_on_lake(container_name, directory_name) -> DataLakeFile:
            # Manually create a file to be written to data lake
            uri = f"s3://{container_name}/{directory_name}/my_file.txt"
            content = b"Hello, AWS S3!"
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

        data_lake_client = S3DataLakeClientResource(
            container_name="my-bucket",
        )
        data_lake_file_system = S3DataLakeFileSystemResource()
        data_lake_io_manager = S3DataLakeIOManager(
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

    def create_resource(self, context: InitResourceContext) -> s3fs.S3FileSystem:
        s3_config = S3StorageSettings()

        client_kwargs = {
            "region_name": s3_config.REGION,
            "endpoint_url": s3_config.ENDPOINT,
        }

        config_kwargs = {
            "connect_timeout": 30,
            "read_timeout": 300,
            "retries": {"max_attempts": 3},
        }

        return s3fs.S3FileSystem(
            key=s3_config.ACCESS_KEY,
            secret=s3_config.SECRET_KEY.get_secret_value(),
            client_kwargs=client_kwargs,
            config_kwargs=config_kwargs,
            anon=False,  # Use credentials, not anonymous access
        )
