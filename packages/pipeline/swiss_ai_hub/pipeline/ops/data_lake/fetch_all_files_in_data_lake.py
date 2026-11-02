from swiss_ai_hub.pipeline.resources.data_lake.base.abstract_data_lake_client import AbstractDataLakeClient
from swiss_ai_hub.pipeline.types.data_lake_listing import DataLakeListing


def fetch_all_files_in_data_lake_no_op(
    data_lake_client: AbstractDataLakeClient,
) -> DataLakeListing:
    """The listing, not only its files, so the observation can report what it skipped."""
    return data_lake_client.list_files()
