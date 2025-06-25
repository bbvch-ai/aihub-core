from typing import List

from azure.storage.filedatalake import FileSystemClient
from dagster import OpExecutionContext, ResourceParam, op

from aihub_pipeline.resources.data_lake.DataLakeResource import DataLakeResource
from aihub_pipeline.types.DataLakeFile import DataLakeFile
from aihub_pipeline.types.SharePointFile import MinimalSharePointFile


@op(code_version="v1")
def fetch_data_lake_files_to_remove(
    context: OpExecutionContext,
    share_point_files: List[MinimalSharePointFile],
    data_lake_resource: DataLakeResource,
    data_lake_client: ResourceParam[FileSystemClient],
) -> List[DataLakeFile]:
    """Fetches all DataLakeFiles that are in the DataLake but no longer in SharePoint."""
    uris_to_exclude = [
        f"{data_lake_resource.container_name}/{data_lake_resource.directory_name}/{file.path.lstrip('/')}"
        for file in share_point_files
    ]

    context.log.info(f"Excluding {len(uris_to_exclude)} URIs from removal")

    data_lake_files = fetch_data_lake_files_without_excluded_uris(
        data_lake_client=data_lake_client,
        data_lake_container_name=data_lake_resource.container_name,
        data_lake_directory_name=data_lake_resource.directory_name,
        excluded_uris=uris_to_exclude,
        figures_directory=data_lake_resource.figures_directory_name,
    )
    context.log.info(f"Found {len(data_lake_files)} data lake files that need to be removed")
    return data_lake_files


def fetch_data_lake_files_without_excluded_uris(
    data_lake_client: ResourceParam[FileSystemClient],
    data_lake_container_name: str,
    data_lake_directory_name: str,
    excluded_uris: List[str] = None,
    figures_directory: str = "__figures__",
) -> List[DataLakeFile]:
    if excluded_uris is None:
        excluded_uris = []

    excluded_uris_set = set(excluded_uris)

    paths = data_lake_client.get_paths(path=f"{data_lake_directory_name}/", recursive=True)
    data_lake_files: List[DataLakeFile] = []

    for path in paths:
        if path.is_directory:
            continue

        if f"/{figures_directory}/" in path.name:
            continue

        path_parts = path.name.split("/")
        if len(path_parts) < 2:
            continue

        document_uri = f"{data_lake_container_name}/{path.name.lstrip('/')}"
        if document_uri in excluded_uris_set:
            continue

        data_lake_file = DataLakeFile.from_uri(uri=document_uri, fs_client=data_lake_client)
        data_lake_files.append(data_lake_file)

    return data_lake_files
