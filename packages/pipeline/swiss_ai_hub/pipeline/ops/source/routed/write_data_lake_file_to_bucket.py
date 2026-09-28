from typing import Any

from dagster import OpExecutionContext, Output, op

from swiss_ai_hub.pipeline.io.s3_data_lake_io_manager import S3DataLakeIOManager
from swiss_ai_hub.pipeline.resources.data_lake.s3.s3_data_lake_client import S3_PROTOCOL_PREFIX
from swiss_ai_hub.pipeline.types.data_lake_file import DataLakeFile
from swiss_ai_hub.pipeline.util.meta_utils import data_lake_file_metadata
from swiss_ai_hub.pipeline.util.run_routing import bucket_from_partition_key
from swiss_ai_hub.pipeline.util.source_updated_notifier import notify_source_updated
from swiss_ai_hub.pipeline.util.store_builders import build_s3_data_lake_client


@op(code_version="v1")
def write_data_lake_file_to_bucket(
    context: OpExecutionContext, content: bytes, metadata: dict[str, Any], uri: str
) -> Output[DataLakeFile]:
    """Lands the file in the data lake of the database its partition names, then tells that database's ingestion
    pipeline — in this order, so the pipeline is never told about a file that is not there yet.

    The write is explicit rather than an IO manager side effect because the announcement must follow it inside one
    step. The returned file carries no content: nothing downstream reads it, and the bytes are already in S3.
    """
    bucket = bucket_from_partition_key(context.partition_key)
    data_lake_file = DataLakeFile.from_content(uri=uri, content=content, metadata=metadata)
    S3DataLakeIOManager.write_data_lake_file(
        build_s3_data_lake_client(bucket, ensure_bucket=False).raw_client, data_lake_file, context
    )
    notify_source_updated(bucket, [uri.removeprefix(S3_PROTOCOL_PREFIX).split("/", 1)[1]])
    return Output(data_lake_file.model_copy(update={"content": None}), metadata=data_lake_file_metadata(data_lake_file))
