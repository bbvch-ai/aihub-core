from aihub_lib.generative_ai.utils.path_utils import create_figures_folder_name
from dagster import OpExecutionContext, Output, ResourceParam, op

from aihub_pipeline.resources.data_lake.base.AbstractDataLakeClient import AbstractDataLakeClient
from aihub_pipeline.types.DataLakeFile import DataLakeFile


@op(code_version="v1")
def delete_data_lake_files_from_data_lake(
    context: OpExecutionContext,
    data_lake_files: list[DataLakeFile],
    data_lake_client: ResourceParam[AbstractDataLakeClient],
) -> Output[list[DataLakeFile]]:
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
