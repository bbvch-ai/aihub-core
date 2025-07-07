from azure.storage.filedatalake import FileSystemClient
from dagster import OpExecutionContext, Output, ResourceParam, op

from aihub_pipeline.types.DataLakeFile import DataLakeFile


@op(code_version="v1")
def delete_data_lake_files_from_data_lake(
    context: OpExecutionContext, data_lake_files: list[DataLakeFile], data_lake_client: ResourceParam[FileSystemClient]
) -> Output[list[DataLakeFile]]:
    for data_lake_file in data_lake_files:
        context.log.info(f"Deleting Data Lake file with uri: {data_lake_file.uri}")
        uri_without_container = data_lake_file.uri.split("/", 1)[1]
        data_lake_client.delete_file(uri_without_container)
        context.log.info(f"Deleted Data Lake file with uri: {data_lake_file.uri}")
    return Output(data_lake_files)
