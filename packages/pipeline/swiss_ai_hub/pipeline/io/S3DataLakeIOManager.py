from urllib.parse import quote, unquote

import s3fs
from dagster import ConfigurableIOManager, InputContext, OutputContext, ResourceDependency
from swiss_ai_hub.core.generative_ai.utils.path_utils import decode_partition_key

from swiss_ai_hub.pipeline.resources.data_lake.s3.S3DataLakeClient import S3DataLakeClient
from swiss_ai_hub.pipeline.types.DataLakeFile import DataLakeFile


class S3DataLakeIOManager(ConfigurableIOManager):
    """Data Lake IO Manager for loading and storing files from/to S3-compatible storage (MinIO).

    This IO Manager is the AWS equivalent of the AzureDataLakeIOManager.
    It handles loading and storing user files from/to S3 buckets.
    This IO Manager is aware of the metadata added to S3 files and always
    returns a DataLakeFile object, not pickled data.

    The S3DataLakeIOManager depends on two other resources:
    - **S3DataLakeClientResource**: Responsible for providing the boto3 S3 client.
    - **S3DataLakeFileSystemResource**: Responsible for providing the S3FileSystem to interact with S3.

    Hence, do NOT use this IO Manager as the default io_manager with the resource key ``"io_manager"``.
    In most cases, you'll want to use it with the resource key ``"data_lake_io_manager"``.

    This IO Manager assumes data partitioning. It can handle two cases:
    - **partitioned asset**: The IO Manager wraps an asset that is partitioned. In this case, the IO Manager
    will load the S3 file corresponding to the partition key.
    - **non-partitioned asset**: The IO Manager wraps an asset that is not partitioned. In this case, the IO Manager
    assumes that the upstream asset was partitioned and will load all S3 files corresponding to all
    partition keys available to the upstream dependency.

    **Note**: The IO Manager currently does not handle the case in which the pipeline is not partitioned
    and only handles a single file.

    Example usage:

    1. Attach an IO manager to a set of assets using the resource key ``"data_lake_io_manager"``

    .. code-block:: python

        from swiss_ai_hub.pipeline.io.S3DataLakeIOManager import S3DataLakeIOManager
        from swiss_ai_hub.pipeline.resources.data_lake.s3.S3DataLakeClientResource import S3DataLakeClientResource
        from swiss_ai_hub.pipeline.resources.data_lake.s3.S3DataLakeFileSystemResource import S3DataLakeFileSystemResource

        from dagster import Definitions, asset

        @asset(partitions_def=my_partition, "io_manager_key=data_lake_io_manager")
        def create_file_on_lake(container_name, directory_name) -> DataLakeFile:
            # Manually create a file to be written to S3
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
            # The input asset will be loaded from S3
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

    data_lake_client: ResourceDependency[S3DataLakeClient]
    data_lake_file_system: ResourceDependency[s3fs.S3FileSystem]
    encode_partition_keys: bool = False

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
                context.log.error(f"No content found for file {data_lake_file.uri}. Cannot write to S3.")
                raise ValueError(f"No content to write for file {data_lake_file.uri}.")

            path = data_lake_file.uri.removeprefix("s3://").lstrip("/")

            # Split into bucket and key
            parts = path.split("/", 1)
            if len(parts) != 2:
                context.log.error(f"Invalid S3 URI format: {data_lake_file.uri}")
                raise ValueError(f"Invalid S3 URI format: {data_lake_file.uri}")

            bucket_name = parts[0]
            object_key = parts[1]

            context.log.info(f"Writing file to S3: s3://{bucket_name}/{object_key}")

            encoded_metadata = self._encode_metadata(data_lake_file.metadata)

            put_params = {
                "Bucket": bucket_name,
                "Key": object_key,
                "Body": data_lake_file.content,
                "Metadata": encoded_metadata,
            }

            if data_lake_file.content_type:
                put_params["ContentType"] = data_lake_file.content_type

            # Write the content to S3 with metadata using put_object
            self.data_lake_client.raw_client.put_object(**put_params)

            context.log.info(f"Successfully wrote file s3://{bucket_name}/{object_key} to S3.")

    def load_input(self, context: InputContext) -> DataLakeFile | list[DataLakeFile]:
        if context.has_partition_key:
            partition_key = context.partition_key
            uri = decode_partition_key(partition_key) if self.encode_partition_keys else partition_key
            return self._load_data_lake_file_from_uri(context, uri)
        else:
            upstream_output = context.upstream_output
            partitions_def = upstream_output.asset_partitions_def
            if partitions_def is not None:
                all_partition_keys = partitions_def.get_partition_keys(dynamic_partitions_store=context.instance)
                data_lake_files = []
                for partition_key in all_partition_keys:
                    uri = decode_partition_key(partition_key) if self.encode_partition_keys else partition_key
                    data_lake_file = self._load_data_lake_file_from_uri(context, uri)
                    data_lake_files.append(data_lake_file)
                return data_lake_files
            else:
                context.log.error("No partition definition found for the upstream asset.")
                raise ValueError("Cannot load data without partition information.")

    def _load_data_lake_file_from_uri(self, context: InputContext, uri: str) -> DataLakeFile:
        """Load a DataLakeFile directly using the partition key as an S3 URI."""
        context.log.info(f"Loading DataLakeFile from URI: {uri}")

        if not uri.startswith("s3://"):
            uri = self.data_lake_client.build_uri(uri)
            context.log.info(f"Constructed full S3 URI: {uri}")

        data_lake_file = self.data_lake_client.create_data_lake_file_from_uri(uri)

        decoded_metadata = self._decode_metadata(data_lake_file.metadata)
        data_lake_file.metadata = decoded_metadata

        return data_lake_file

    @staticmethod
    def _encode_metadata(metadata: dict) -> dict:
        return {quote(key, safe=""): quote(str(value), safe=":/?&=") for key, value in metadata.items()}

    @staticmethod
    def _decode_metadata(metadata: dict) -> dict:
        return {unquote(key): unquote(value) for key, value in metadata.items()}
