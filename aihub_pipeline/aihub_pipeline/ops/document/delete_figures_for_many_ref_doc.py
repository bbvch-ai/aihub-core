from typing import List

from azure.storage.filedatalake import FileSystemClient
from dagster import OpExecutionContext, op, ResourceParam

from aihub_pipeline.resources.data_lake.DataLakeResource import DataLakeResource
from aihub_pipeline.types.RefDocDocument import RefDocDocument
from aihub_pipeline.util.path_utils import create_data_lake_figures_folder_name, get_data_lake_client_figure_path


@op(code_version="v1")
def delete_figures_for_many_ref_doc(
    context: OpExecutionContext,
    ref_docs: List[RefDocDocument],
    data_lake_client: ResourceParam[FileSystemClient],
    data_lake_resource: ResourceParam[DataLakeResource],
) -> List[RefDocDocument]:
    """Deletes figures associated with each RefDocDocument from the data lake."""
    for ref_doc in ref_docs:
        figures_folder = create_data_lake_figures_folder_name(ref_doc.uri, data_lake_resource.figures_directory_name)
        figures_folder = get_data_lake_client_figure_path(figures_folder)
        paths = data_lake_client.get_paths(figures_folder + "/")

        for blob in paths:
            data_lake_client.delete_file(blob.name)

        data_lake_client.delete_directory(figures_folder)

    context.log.info(f"All figures were deleted for {len(ref_docs)} documents.")
    return ref_docs
