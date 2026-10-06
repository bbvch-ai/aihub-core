from dagster import OpExecutionContext, Output, ResourceParam, op
from swiss_ai_hub.core.generative_ai.utils.path_utils import create_figures_folder_name

from swiss_ai_hub.pipeline.resources.data_lake.base.abstract_data_lake_client import AbstractDataLakeClient


@op(code_version="v3")
def delete_data_lake_files_from_data_lake(
    context: OpExecutionContext,
    uris: list[str],
    data_lake_client: ResourceParam[AbstractDataLakeClient],
) -> Output[list[str]]:
    """Delete files from the data lake storage.

    The RefDoc is left for the ingestion pipeline's removal run: it finds the documents to remove by their
    record, so deleting the record here would strand the document's vector nodes.
    """
    for uri in uris:
        context.log.info(f"Deleting Data Lake file with uri: {uri}")
        data_lake_client.delete_file(uri=uri)
        context.log.info(f"Deleted Data Lake file with uri: {uri}")

        figures_folder = create_figures_folder_name(uri=uri)
        if data_lake_client.directory_exists(directory_path=figures_folder):
            context.log.info(f"Deleting figures folder: {figures_folder}")
            data_lake_client.delete_directory(directory_path=figures_folder)
            context.log.info(f"Deleted figures folder: {figures_folder}")

    return Output(uris)
