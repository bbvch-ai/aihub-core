import boto3
from dagster import InitResourceContext
from swiss_ai_hub.core.infrastructure import S3StorageSettings

from swiss_ai_hub.pipeline.resources.data_lake.base.abstract_data_lake_client_resource import (
    AbstractDataLakeClientResource,
)
from swiss_ai_hub.pipeline.resources.data_lake.s3.s3_data_lake_client import S3DataLakeClient


class S3DataLakeClientResource(AbstractDataLakeClientResource[S3DataLakeClient]):
    """
    A resource that provides a boto3 S3 client for interacting with S3-compatible storage (MinIO).
    The S3 client is suitable when you need granular control over storage operations,
    such as setting specific permissions or metadata.

    You can use this client SDK when you want to get specific details of a file like its metadata, when it
    last changed, etc.

    You should not use this client SDK when you want to open the file and read its contents. For that, you should use
    the S3FileSystem provided by the S3DataLakeFileSystemResource.

    **Note**: When using the client SDK, ensure you have proper IAM permissions for the S3 buckets you're accessing.

    Example usage:

    1. Directly interact with the S3 data lake:

    .. code-block:: python

        from swiss_ai_hub.pipeline.resources.data_lake.s3.s3_data_lake_client_resource import S3DataLakeClientResource

        from dagster import Definitions, asset

        @asset
        def asset1(data_lake_client: ResourceParam[boto3.client]):
            # List objects in a bucket
            response = data_lake_client.list_objects_v2(
                Bucket='my-bucket',
                Prefix='my-prefix/'
            )
            for obj in response.get('Contents', []):
                print(obj['Key'])

        defs = Definitions(
            assets=[asset1],
            resources={
                "data_lake_client": S3DataLakeClientResource(container_name="my-bucket")
            }
        )

    2. Use the data lake client as part of a data lake io manager:

    .. code-block:: python

        from swiss_ai_hub.pipeline.io.s3_data_lake_io_manager import S3DataLakeIOManager
        from swiss_ai_hub.pipeline.resources.data_lake.s3.s3_data_lake_client_resource import (
            S3DataLakeClientResource,
        )
        from swiss_ai_hub.pipeline.resources.data_lake.s3.s3_data_lake_file_system_resource import (
            S3DataLakeFileSystemResource,
        )

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

        data_lake_client = S3DataLakeClientResource(container_name="my-bucket")

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

    container_name: str

    def create_resource(self, context: InitResourceContext) -> S3DataLakeClient:
        s3_config = S3StorageSettings()

        s3_client = boto3.client(
            "s3",
            aws_access_key_id=s3_config.ACCESS_KEY,
            aws_secret_access_key=s3_config.SECRET_KEY.get_secret_value(),
            region_name=s3_config.REGION,
            endpoint_url=s3_config.ENDPOINT,
        )
        return S3DataLakeClient(self.container_name, s3_client)
