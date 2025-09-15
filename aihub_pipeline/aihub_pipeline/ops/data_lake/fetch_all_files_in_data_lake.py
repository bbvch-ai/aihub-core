from dagster import ResourceParam, op

from aihub_pipeline.resources.data_lake.base.AbstractDataLakeClient import AbstractDataLakeClient
from aihub_pipeline.resources.data_lake.DataLakeResource import DataLakeResource
from aihub_pipeline.types.DataLakeFile import DataLakeFile


def fetch_all_files_in_data_lake_no_op(
    data_lake_client: ResourceParam[AbstractDataLakeClient],
    data_lake_resource: DataLakeResource,
) -> list[DataLakeFile]:
    """Fetches all files using the clean AbstractDataLakeClient interface."""
    return data_lake_client.get_all_files(figures_directory_name=data_lake_resource.figures_directory_name)


@op(code_version="v1")
def fetch_all_files_in_data_lake(
    data_lake_client: ResourceParam[AbstractDataLakeClient],
    data_lake_resource: DataLakeResource,
) -> list[DataLakeFile]:
    """Fetches all files in the data lake for a given namespace."""
    return fetch_all_files_in_data_lake_no_op(
        data_lake_client=data_lake_client,
        data_lake_resource=data_lake_resource,
    )
