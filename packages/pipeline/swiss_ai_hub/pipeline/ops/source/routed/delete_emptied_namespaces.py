from dagster import In, OpExecutionContext, Output, op
from swiss_ai_hub.core.persistence import BucketEntity, NamespaceEntity

from swiss_ai_hub.pipeline.resources.data_lake.s3.s3_data_lake_client import S3_PROTOCOL_PREFIX
from swiss_ai_hub.pipeline.types.source_file import MinimalSourceFile
from swiss_ai_hub.pipeline.util.bucket_utils import ensure_main_db_connection
from swiss_ai_hub.pipeline.util.run_routing import bucket_from_run_tag
from swiss_ai_hub.pipeline.util.store_builders import build_s3_data_lake_client


@op(code_version="v1", ins={"removed_uris": In(), "source_files": In(default_value=[])})
def delete_emptied_namespaces(
    context: OpExecutionContext, removed_uris: list[str], source_files: list[MinimalSourceFile]
) -> Output[list[str]]:
    """Deletes the namespace row of every folder of this run's database that holds no file any more.

    The source pipeline creates a namespace per top-level folder but only ever removes files, and a sourced database
    refuses manual namespace deletion, so a folder deleted or emptied at the source would otherwise linger forever.
    Only the row goes: the folder's documents, figures and vectors are removed per file by the ingestion pipeline,
    which finds them by the namespace name each document carries. Nothing is torn down, so a folder re-created at the
    source simply gets a fresh row from the next observation. A row flagged ``deleting`` is a manual deletion in
    progress and stays with the teardown, which still has its files to remove.

    A folder the source still lists counts as occupied even while the data lake has none of its files: rclone writes
    each file in a run of its own, which a file replacing the folder's last one may not have finished yet. The
    structured pipeline writes within this run and passes no files.
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
        context.log.info(f"'{bucket}': folder '{namespace.folder_name}' is empty, deleting its namespace")
        NamespaceEntity.delete_namespace(str(namespace.id))

    return Output(removed_uris, metadata={"emptied_namespaces": [namespace.namespace_name for namespace in emptied]})
