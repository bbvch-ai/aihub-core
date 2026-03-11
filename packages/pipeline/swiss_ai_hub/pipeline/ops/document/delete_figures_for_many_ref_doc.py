from dagster import OpExecutionContext, ResourceParam, op
from swiss_ai_hub.core.generative_ai.utils.path_utils import create_figures_folder_name

from swiss_ai_hub.pipeline.resources.data_lake.base.abstract_data_lake_client import AbstractDataLakeClient
from swiss_ai_hub.pipeline.types.ref_doc_document import RefDocDocument


@op(code_version="v1")
def delete_figures_for_many_ref_doc(
    context: OpExecutionContext,
    ref_docs: list[RefDocDocument],
    data_lake_client: ResourceParam[AbstractDataLakeClient],
) -> list[RefDocDocument]:
    """Deletes figures associated with each RefDocDocument from the data lake."""
    for ref_doc in ref_docs:
        figures_folder = create_figures_folder_name(uri=ref_doc.uri)
        if data_lake_client.directory_exists(directory_path=figures_folder):
            paths = data_lake_client.list_directory_contents(directory_path=figures_folder)
            for path in paths:
                if not path.endswith("/"):
                    file_uri = data_lake_client.build_uri(file_path=path)
                    data_lake_client.delete_file(uri=file_uri)

            data_lake_client.delete_directory(directory_path=figures_folder)
        else:
            context.log.info(f"Figures directory '{figures_folder}' for {ref_doc.uri} not found, skipping deletion.")

    context.log.info(f"All figures were deleted for {len(ref_docs)} documents.")
    return ref_docs
