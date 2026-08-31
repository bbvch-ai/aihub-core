from dagster import ConfigurableIOManager, InputContext, OutputContext

from swiss_ai_hub.pipeline.io.s3_data_lake_io_manager import S3DataLakeIOManager
from swiss_ai_hub.pipeline.types.data_lake_file import DataLakeFile
from swiss_ai_hub.pipeline.util.partition_utils import split_composite_partition_key
from swiss_ai_hub.pipeline.util.run_routing import bucket_from_run_tag
from swiss_ai_hub.pipeline.util.store_builders import build_s3_data_lake_client


class RoutedS3DataLakeIOManager(ConfigurableIOManager):
    """Read-only S3 data lake IO manager for the RAG pipeline, routed per run by bucket.

    The RAG pipeline shares one partition registry across every knowledge database, so partition
    keys are composite ``{bucket}|{file_uri}``. On the partitioned read this manager recovers ``bucket`` from
    the key and builds a bucket-scoped client — auto-materialized runs carry no run tag, so the key is the
    only routing signal. On the non-partitioned ``removed_documents`` load there is no partition key, so the
    bucket comes from the ``aihub/bucket`` run tag and the upstream keys are filtered to that bucket.

    Stage 2 never writes to the data lake (the observable source asset only reads), so ``handle_output`` is
    intentionally unsupported.
    """

    encode_partition_keys: bool = True

    def handle_output(self, context: OutputContext, obj: DataLakeFile | list[DataLakeFile]) -> None:
        raise NotImplementedError("RoutedS3DataLakeIOManager is read-only; the data lake is populated upstream.")

    def load_input(self, context: InputContext) -> DataLakeFile | list[DataLakeFile]:
        if context.has_partition_key:
            bucket, uri = split_composite_partition_key(context.partition_key, encode=self.encode_partition_keys)
            return self._load_data_lake_file(bucket, uri, context)

        bucket = bucket_from_run_tag(context)
        bucket_prefix = f"{bucket}|"
        partitions_def = context.upstream_output.asset_partitions_def
        if partitions_def is None:
            raise ValueError("Cannot load data without partition information.")

        all_partition_keys = partitions_def.get_partition_keys(dynamic_partitions_store=context.instance)
        uris = [
            split_composite_partition_key(key, encode=self.encode_partition_keys)[1]
            for key in all_partition_keys
            if key.startswith(bucket_prefix)
        ]
        context.log.info(f"Loading {len(uris)} DataLakeFile(s) from bucket '{bucket}'")

        # One client and one batched call: resolving each file separately re-derives the namespace of the
        # directory it sits in, which is a database round-trip per file over the whole corpus.
        client = build_s3_data_lake_client(bucket, ensure_bucket=False)
        data_lake_files = client.create_data_lake_files_from_uris(uris)
        for data_lake_file in data_lake_files:
            data_lake_file.metadata = S3DataLakeIOManager._decode_metadata(data_lake_file.metadata)
        return data_lake_files

    def _load_data_lake_file(self, bucket: str, uri: str, context: InputContext) -> DataLakeFile:
        context.log.info(f"Loading DataLakeFile from URI: {uri} (bucket: {bucket})")
        client = build_s3_data_lake_client(bucket, ensure_bucket=False)
        data_lake_file = client.create_data_lake_file_from_uri(uri)
        data_lake_file.metadata = S3DataLakeIOManager._decode_metadata(data_lake_file.metadata)
        return data_lake_file
