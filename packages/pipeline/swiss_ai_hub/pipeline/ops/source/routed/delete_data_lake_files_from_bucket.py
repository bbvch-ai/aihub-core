from dagster import OpExecutionContext, Output, op
from swiss_ai_hub.core.generative_ai.utils.path_utils import create_figures_folder_name

from swiss_ai_hub.pipeline.util.run_routing import bucket_from_run_tag
from swiss_ai_hub.pipeline.util.store_builders import build_s3_data_lake_client


@op(code_version="v2")
def delete_data_lake_files_from_bucket(context: OpExecutionContext, uris: list[str]) -> Output[list[str]]:
    """Removes the objects and their figures from this run's database.

    Doc store and vector store are left to the ingestion pipeline: it is the single writer of those stores, and
    the announcement that follows makes it reconcile them against the data lake.
    """
    client = build_s3_data_lake_client(bucket_from_run_tag(context), ensure_bucket=False)
    for uri in uris:
        context.log.info(f"Deleting data lake file {uri}")
        client.delete_file(uri=uri)
        figures_folder = create_figures_folder_name(uri=uri)
        if client.directory_exists(directory_path=figures_folder):
            client.delete_directory(directory_path=figures_folder)
    return Output(uris)
