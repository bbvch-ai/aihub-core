from collections.abc import Sequence
from urllib.parse import quote, unquote

import boto3
import s3fs
from dagster import ConfigurableIOManager, InputContext, OpExecutionContext, OutputContext, ResourceDependency
from swiss_ai_hub.core.generative_ai.utils.path_utils import decode_partition_key

from swiss_ai_hub.pipeline.resources.data_lake.s3.s3_data_lake_client import S3_PROTOCOL_PREFIX, S3DataLakeClient
from swiss_ai_hub.pipeline.types.data_lake_file import DataLakeFile


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
        for data_lake_file in self.as_data_lake_files(obj):
            self.write_data_lake_file(self.data_lake_client.raw_client, data_lake_file, context)

    @staticmethod
    def as_data_lake_files(obj: object) -> list[DataLakeFile]:
        if isinstance(obj, DataLakeFile):
            return [obj]
        if isinstance(obj, list) and all(isinstance(item, DataLakeFile) for item in obj):
            return obj
        raise ValueError("Expected a DataLakeFile or a list of DataLakeFiles.")

    @staticmethod
    def write_data_lake_file(
        raw_client: boto3.client, data_lake_file: DataLakeFile, context: OpExecutionContext | OutputContext
    ) -> None:
        """Puts one file with its metadata; the bucket is whatever the URI names, so a routed pipeline can share it."""
        if data_lake_file.content is None:
            raise ValueError(f"No content to write for file {data_lake_file.uri}.")

        path = data_lake_file.uri.removeprefix(S3_PROTOCOL_PREFIX).lstrip("/")
        parts = path.split("/", 1)
        if len(parts) != 2:
            raise ValueError(f"Invalid S3 URI format: {data_lake_file.uri}")
        bucket_name, object_key = parts

        context.log.info(f"Writing file to S3: {S3_PROTOCOL_PREFIX}{bucket_name}/{object_key}")
        put_params = {
            "Bucket": bucket_name,
            "Key": object_key,
            "Body": data_lake_file.content,
            "Metadata": S3DataLakeIOManager._encode_metadata(data_lake_file.metadata),
        }
        if data_lake_file.content_type:
            put_params["ContentType"] = data_lake_file.content_type
        raw_client.put_object(**put_params)
        context.log.info(f"Successfully wrote file {S3_PROTOCOL_PREFIX}{bucket_name}/{object_key} to S3.")

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
                return self._load_data_lake_files_from_partition_keys(context, all_partition_keys)
            else:
                context.log.error("No partition definition found for the upstream asset.")
                raise ValueError("Cannot load data without partition information.")

    def _load_data_lake_files_from_partition_keys(
        self, context: InputContext, partition_keys: Sequence[str]
    ) -> list[DataLakeFile]:
        """Loads every partition in one go so namespaces resolve once per directory.

        This is the whole-corpus load the removal job performs after every observation, where a
        per-file namespace lookup costs as much as it did in the observation itself.
        """
        uris = [
            self._to_full_uri(decode_partition_key(partition_key) if self.encode_partition_keys else partition_key)
            for partition_key in partition_keys
        ]
        context.log.info(f"Loading {len(uris)} DataLakeFile(s) from partition keys")

        data_lake_files = self.data_lake_client.create_data_lake_files_from_uris(uris)
        for data_lake_file in data_lake_files:
            data_lake_file.metadata = self._decode_metadata(data_lake_file.metadata)

        return data_lake_files

    def _to_full_uri(self, uri: str) -> str:
        return uri if uri.startswith(S3_PROTOCOL_PREFIX) else self.data_lake_client.build_uri(uri)

    def _load_data_lake_file_from_uri(self, context: InputContext, uri: str) -> DataLakeFile:
        """Load a DataLakeFile directly using the partition key as an S3 URI."""
        context.log.info(f"Loading DataLakeFile from URI: {uri}")

        if not uri.startswith(S3_PROTOCOL_PREFIX):
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
