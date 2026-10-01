from dagster import OpExecutionContext, ResourceParam, op

from swiss_ai_hub.pipeline.resources.data_lake.base.abstract_data_lake_client import AbstractDataLakeClient
from swiss_ai_hub.pipeline.resources.data_lake.data_lake_resource import DataLakeResource
from swiss_ai_hub.pipeline.types.source_file import MinimalSourceFile


@op(code_version="v2")
def fetch_data_lake_files_to_remove(
    context: OpExecutionContext,
    source_files: list[MinimalSourceFile],
    data_lake_client: ResourceParam[AbstractDataLakeClient],
    data_lake_resource: ResourceParam[DataLakeResource],
) -> list[str]:
    """
    URIs of data lake files that should be removed because they no longer exist in the source.

    This generic operation works with any source file type (SharePoint, local file system, etc.)
    that implements the MinimalSourceFile interface. Only URIs are compared, with no namespace lookup,
    so a folder whose namespace collides with another's cannot block the removal that repairs it.
    """
    # to ensure the path matches how files were originally stored
    uris_to_exclude = {
        data_lake_client.build_uri(file_path=data_lake_resource.build_path(file.path)) for file in source_files
    }

    context.log.info(f"Excluding {len(uris_to_exclude)} URIs from removal")

    uris_to_remove = [uri for uri in data_lake_client.list_ingestible_uris() if uri not in uris_to_exclude]
    context.log.info(f"Found {len(uris_to_remove)} data lake files that need to be removed")
    return uris_to_remove
