from dagster import OpExecutionContext, ResourceParam, op

from aihub_pipeline.resources.data_lake.base.AbstractDataLakeClient import AbstractDataLakeClient
from aihub_pipeline.resources.data_lake.DataLakeResource import DataLakeResource
from aihub_pipeline.types.DataLakeFile import DataLakeFile
from aihub_pipeline.types.SharePointFile import MinimalSharePointFile


@op(code_version="v1")
def fetch_data_lake_files_to_remove(
    context: OpExecutionContext,
    share_point_files: list[MinimalSharePointFile],
    data_lake_resource: DataLakeResource,
    data_lake_client: ResourceParam[AbstractDataLakeClient],
) -> list[DataLakeFile]:
    """Fetches all DataLakeFiles that are in the DataLake but no longer in SharePoint."""
    uris_to_exclude = [
        f"{data_lake_resource.container_name}/{data_lake_resource.directory_name}/{file.path.lstrip('/')}"
        for file in share_point_files
    ]

    context.log.info(f"Excluding {len(uris_to_exclude)} URIs from removal")

    data_lake_files = fetch_data_lake_files_without_excluded_uris(
        data_lake_client=data_lake_client,
        excluded_uris=uris_to_exclude,
    )
    context.log.info(f"Found {len(data_lake_files)} data lake files that need to be removed")
    return data_lake_files


def fetch_data_lake_files_without_excluded_uris(
    data_lake_client: ResourceParam[AbstractDataLakeClient],
    excluded_uris: list[str] | None = None,
) -> list[DataLakeFile]:
    if excluded_uris is None:
        excluded_uris = []

    excluded_uris_set = set(excluded_uris)

    all_files = data_lake_client.get_all_files()

    data_lake_files: list[DataLakeFile] = []
    for data_lake_file in all_files:
        if data_lake_file.uri in excluded_uris_set:
            continue
        data_lake_files.append(data_lake_file)

    return data_lake_files
