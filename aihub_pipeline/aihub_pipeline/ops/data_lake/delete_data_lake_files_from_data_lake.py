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
        data_lake_client.delete_file(data_lake_file.uri)
        context.log.info(f"Deleted Data Lake file with uri: {data_lake_file.uri}")
    return Output(data_lake_files)
