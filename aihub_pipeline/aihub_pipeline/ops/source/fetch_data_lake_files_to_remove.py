from dagster import OpExecutionContext, ResourceParam, op

from aihub_pipeline.resources.data_lake.base.AbstractDataLakeClient import AbstractDataLakeClient
from aihub_pipeline.resources.data_lake.DataLakeResource import DataLakeResource
from aihub_pipeline.types.DataLakeFile import DataLakeFile
from aihub_pipeline.types.SourceFile import MinimalSourceFile


@op(code_version="v1")
def fetch_data_lake_files_to_remove(
    context: OpExecutionContext,
    source_files: list[MinimalSourceFile],
    data_lake_client: ResourceParam[AbstractDataLakeClient],
    data_lake_resource: ResourceParam[DataLakeResource],
) -> list[DataLakeFile]:
    """
    Fetch data lake files that should be removed because they no longer exist in the source.

    This generic operation works with any source file type (SharePoint, local file system, etc.)
    that implements the MinimalSourceFile interface. It compares files in the data lake with
    files from the source system and identifies files that have been deleted from the source
    and should be removed from the data lake.

    """
    # Build URIs using the client's build_uri method combined with data_lake_resource.build_path
    # to ensure the path matches how files were originally stored
    uris_to_exclude = [
        data_lake_client.build_uri(file_path=data_lake_resource.build_path(file.path)) for file in source_files
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
    excluded_uris: list[str],
) -> list[DataLakeFile]:
    excluded_uris_set = set(excluded_uris)

    all_files = data_lake_client.get_all_files()

    data_lake_files: list[DataLakeFile] = []
    for data_lake_file in all_files:
        if data_lake_file.uri in excluded_uris_set:
            continue
        data_lake_files.append(data_lake_file)

    return data_lake_files
