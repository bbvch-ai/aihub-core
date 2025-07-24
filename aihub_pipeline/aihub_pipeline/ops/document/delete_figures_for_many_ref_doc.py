from aihub_lib.generative_ai.utils.path_utils import create_figures_folder_name
from dagster import OpExecutionContext, ResourceParam, op

from aihub_pipeline.resources.data_lake.base.AbstractDataLakeClient import AbstractDataLakeClient
from aihub_pipeline.resources.data_lake.DataLakeResource import DataLakeResource
from aihub_pipeline.types.RefDocDocument import RefDocDocument


@op(code_version="v1")
def delete_figures_for_many_ref_doc(
    context: OpExecutionContext,
    ref_docs: list[RefDocDocument],
    data_lake_client: ResourceParam[AbstractDataLakeClient],
    data_lake_resource: ResourceParam[DataLakeResource],
) -> list[RefDocDocument]:
    """Deletes figures associated with each RefDocDocument from the data lake."""
    for ref_doc in ref_docs:
        figures_folder = create_figures_folder_name(ref_doc.uri, data_lake_resource.figures_directory_name)
        if data_lake_client.directory_exists(figures_folder):
            # Get all files in the directory
            paths = data_lake_client.list_directory_contents(figures_folder)
            for path in paths:
                # Delete each file (list_directory_contents returns full paths)
                if not path.endswith("/"):
                    data_lake_client.delete_file(path)

            # Delete the directory itself
            data_lake_client.delete_directory(figures_folder)
        else:
            context.log.info(f"Figures directory '{figures_folder}' for {ref_doc.uri} not found, skipping deletion.")

    context.log.info(f"All figures were deleted for {len(ref_docs)} documents.")
    return ref_docs
