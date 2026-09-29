from dagster import OpExecutionContext, op

from swiss_ai_hub.pipeline.types.source_file import MinimalSourceFile
from swiss_ai_hub.pipeline.util.run_routing import bucket_from_run_tag
from swiss_ai_hub.pipeline.util.store_builders import build_s3_data_lake_client


@op(code_version="v2")
def fetch_bucket_files_to_remove(context: OpExecutionContext, source_files: list[MinimalSourceFile]) -> list[str]:
    """URIs of data lake files of this run's database that the source no longer has.

    A whole-bucket diff is correct here: a sourced database is filled by its source alone, so anything the source
    does not list is an orphan. Only URIs are compared, with no namespace lookup, so a folder whose namespace
    collides with another's cannot block the removal that repairs it after a rename at the source.
    """
    bucket = bucket_from_run_tag(context)
    client = build_s3_data_lake_client(bucket, ensure_bucket=False)
    kept = {client.build_uri(file.path.lstrip("/")) for file in source_files}
    to_remove = [uri for uri in client.list_ingestible_uris() if uri not in kept]
    context.log.info(f"'{bucket}': {len(kept)} file(s) at the source, {len(to_remove)} orphan(s) to remove")
    return to_remove
