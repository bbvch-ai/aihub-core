from dagster import ResourceParam, op

from swiss_ai_hub.pipeline.resources.data_lake.base.abstract_data_lake_client import AbstractDataLakeClient
from swiss_ai_hub.pipeline.types.data_lake_file import DataLakeFile


def fetch_all_files_in_data_lake_no_op(
    data_lake_client: ResourceParam[AbstractDataLakeClient],
) -> list[DataLakeFile]:
    """Fetches all files using the clean AbstractDataLakeClient interface."""
    return data_lake_client.get_all_files()


@op(code_version="v1")
def fetch_all_files_in_data_lake(
    data_lake_client: ResourceParam[AbstractDataLakeClient],
) -> list[DataLakeFile]:
    """Fetches all files in the data lake for a given namespace."""
    return fetch_all_files_in_data_lake_no_op(
        data_lake_client=data_lake_client,
    )
