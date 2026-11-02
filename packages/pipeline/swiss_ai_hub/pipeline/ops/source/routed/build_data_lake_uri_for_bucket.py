from dagster import OpExecutionContext, op

from swiss_ai_hub.pipeline.resources.data_lake.s3.s3_data_lake_client import S3_PROTOCOL_PREFIX
from swiss_ai_hub.pipeline.types.source_file import SourceFile
from swiss_ai_hub.pipeline.util.run_routing import bucket_from_partition_key


@op(code_version="v1")
def build_data_lake_uri_for_bucket(context: OpExecutionContext, source_file: SourceFile) -> str:
    """``s3://{bucket}/{remote path}`` — no directory prefix, so the source's top-level folders become namespaces."""
    bucket = bucket_from_partition_key(context.partition_key)
    return f"{S3_PROTOCOL_PREFIX}{bucket}/{source_file.path.lstrip('/')}"
