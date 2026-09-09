from dagster import OpExecutionContext, Output, op

from swiss_ai_hub.pipeline.resources.data_lake.s3.s3_data_lake_client import S3_PROTOCOL_PREFIX
from swiss_ai_hub.pipeline.types.data_lake_file import DataLakeFile
from swiss_ai_hub.pipeline.util.run_routing import bucket_from_run_tag
from swiss_ai_hub.pipeline.util.source_updated_notifier import notify_source_updated


@op(code_version="v1")
def announce_removed_files(
    context: OpExecutionContext, removed_files: list[DataLakeFile]
) -> Output[list[DataLakeFile]]:
    """One event per removed file, so the ingestion pipeline drops the document the way it does after a UI delete."""
    bucket = bucket_from_run_tag(context)
    object_keys = [file.uri.removeprefix(S3_PROTOCOL_PREFIX).split("/", 1)[1] for file in removed_files]
    notify_source_updated(bucket, object_keys)
    return Output(removed_files)
