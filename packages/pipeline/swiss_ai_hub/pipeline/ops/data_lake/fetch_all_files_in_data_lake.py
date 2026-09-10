from swiss_ai_hub.pipeline.resources.data_lake.base.abstract_data_lake_client import AbstractDataLakeClient
from swiss_ai_hub.pipeline.types.data_lake_file import DataLakeFile


def fetch_all_files_in_data_lake_no_op(
    data_lake_client: AbstractDataLakeClient,
) -> list[DataLakeFile]:
    """Fetches all files using the clean AbstractDataLakeClient interface."""
    return data_lake_client.get_all_files()
