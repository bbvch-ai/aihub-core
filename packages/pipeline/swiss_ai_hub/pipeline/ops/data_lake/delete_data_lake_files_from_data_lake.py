from dagster import OpExecutionContext, Output, ResourceParam, op
from llama_index.core.storage.docstore.keyval_docstore import KVDocumentStore
from swiss_ai_hub.core.generative_ai.utils.path_utils import create_figures_folder_name

from swiss_ai_hub.pipeline.resources.data_lake.base.abstract_data_lake_client import AbstractDataLakeClient
from swiss_ai_hub.pipeline.types.data_lake_file import DataLakeFile
from swiss_ai_hub.pipeline.util.id_utils import uri_to_id


@op(code_version="v2")
def delete_data_lake_files_from_data_lake(
    context: OpExecutionContext,
    data_lake_files: list[DataLakeFile],
    data_lake_client: ResourceParam[AbstractDataLakeClient],
    doc_store: ResourceParam[KVDocumentStore],
) -> Output[list[DataLakeFile]]:
    """Delete files from the data lake storage and clean up RefDoc from docstore.

    Manual deletion directly from S3/storage is not supported. Always use this pipeline
    op to ensure RefDoc documents are properly cleaned up from the docstore.
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

        # Clean up the RefDoc from docstore
        try:
            doc_id = uri_to_id(data_lake_file.uri)
            doc_store.delete_document(doc_id)
            context.log.info(f"Deleted RefDoc from docstore for: {data_lake_file.uri}")
        except Exception as e:
            context.log.warning(f"Failed to delete RefDoc from docstore for {data_lake_file.uri}: {e}")

    return Output(data_lake_files)
