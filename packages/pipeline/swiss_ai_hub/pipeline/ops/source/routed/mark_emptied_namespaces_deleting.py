from dagster import In, OpExecutionContext, Output, op
from swiss_ai_hub.core.persistence import BucketEntity, NamespaceEntity

from swiss_ai_hub.pipeline.resources.data_lake.s3.s3_data_lake_client import S3_PROTOCOL_PREFIX
from swiss_ai_hub.pipeline.types.source_file import MinimalSourceFile
from swiss_ai_hub.pipeline.util.bucket_utils import ensure_main_db_connection
from swiss_ai_hub.pipeline.util.run_routing import bucket_from_run_tag
from swiss_ai_hub.pipeline.util.store_builders import build_s3_data_lake_client


@op(code_version="v2", ins={"removed_uris": In(), "source_files": In(default_value=[])})
def mark_emptied_namespaces_deleting(
    context: OpExecutionContext, removed_uris: list[str], source_files: list[MinimalSourceFile]
) -> Output[list[str]]:
    """Flags for teardown every namespace of this run's database whose folder holds no file any more.

    The source pipeline creates a namespace per top-level folder but only ever removes files, and a sourced database
    refuses manual namespace deletion, so a folder deleted or emptied at the source would otherwise linger forever.
    Flagging rather than deleting hands vectors, records and the row to the teardown sensor, which retries until done.

    A folder the source still lists counts as occupied even while the data lake has none of its files: rclone writes
    each file in a run of its own, which a file replacing the folder's last one may not have finished yet, and the
    teardown would delete it once it lands. The structured pipeline writes within this run and passes no files.
    """
    bucket = bucket_from_run_tag(context)
    client = build_s3_data_lake_client(bucket, ensure_bucket=False)
    occupied_folders = {uri.removeprefix(S3_PROTOCOL_PREFIX).split("/")[1] for uri in client.list_ingestible_uris()}
    occupied_folders |= {file.path.lstrip("/").split("/")[0] for file in source_files}

    ensure_main_db_connection()
    bucket_id = str(BucketEntity.get_bucket_by_bucket_name(bucket).id)
    emptied = [
        namespace
        for namespace in NamespaceEntity.get_namespaces_by_bucket(bucket_id)
        if not namespace.deleting and namespace.folder_name not in occupied_folders
    ]
    for namespace in emptied:
        context.log.info(f"'{bucket}': folder '{namespace.folder_name}' is empty, flagging its namespace for teardown")
        NamespaceEntity.mark_deleting(str(namespace.id))

    return Output(removed_uris, metadata={"emptied_namespaces": [namespace.namespace_name for namespace in emptied]})
