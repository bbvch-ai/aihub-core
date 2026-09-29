from dagster import OpExecutionContext, Output, ResourceParam, op
from swiss_ai_hub.core.generative_ai.utils.path_utils import create_figures_folder_name

from swiss_ai_hub.pipeline.resources.data_lake.base.abstract_data_lake_client import AbstractDataLakeClient
from swiss_ai_hub.pipeline.types.data_lake_file import DataLakeFile


@op(code_version="v3")
def delete_data_lake_files_from_data_lake(
    context: OpExecutionContext,
    data_lake_files: list[DataLakeFile],
    data_lake_client: ResourceParam[AbstractDataLakeClient],
) -> Output[list[DataLakeFile]]:
    """Delete files from the data lake storage.

    The RefDoc is left for the ingestion pipeline's removal run: it finds the documents to remove by their
    record, so deleting the record here would strand the document's vector nodes.
    """
    for data_lake_file in data_lake_files:
        context.log.info(f"Deleting Data Lake file with uri: {data_lake_file.uri}")
        data_lake_client.delete_file(uri=data_lake_file.uri)
        context.log.info(f"Deleted Data Lake file with uri: {data_lake_file.uri}")

        figures_folder = create_figures_folder_name(uri=data_lake_file.uri)
        if data_lake_client.directory_exists(directory_path=figures_folder):
            context.log.info(f"Deleting figures folder: {figures_folder}")
            data_lake_client.delete_directory(directory_path=figures_folder)
            context.log.info(f"Deleted figures folder: {figures_folder}")

    return Output(data_lake_files)
