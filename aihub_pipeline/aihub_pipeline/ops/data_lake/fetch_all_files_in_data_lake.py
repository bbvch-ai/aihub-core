from typing import List

from azure.storage.filedatalake import FileSystemClient
from dagster import OpExecutionContext, ResourceParam, op

from aihub_pipeline.resources.organization.NamespaceResource import NamespaceResource
from aihub_pipeline.types.DataLakeFile import DataLakeFile


def fetch_all_files_in_data_lake_no_op(
    context: OpExecutionContext,
    data_lake_client: ResourceParam[FileSystemClient],
    namespace: NamespaceResource,
) -> List[DataLakeFile]:
    paths = data_lake_client.get_paths(path=f"{namespace.name}/", recursive=True)
    data_lake_files: List[DataLakeFile] = []

    for path in paths:
        context.log.info(f"Traversing '{path.name}'")

        if path.is_directory:
            continue

        path_parts = path.name.split("/")
        document_namespace = path_parts[0]

        if len(path_parts) == 1 or document_namespace != namespace.name:
            continue

        document_uri = f"{namespace.organization}/{path.name.lstrip('/')}"
        context.log.info(f"Found document with uri '{document_uri}'")
        data_lake_file = DataLakeFile.from_uri(uri=document_uri, fs_client=data_lake_client)
        data_lake_files.append(data_lake_file)
    return data_lake_files


@op(code_version="v1")
def fetch_all_files_in_data_lake(
    context: OpExecutionContext,
    data_lake_client: ResourceParam[FileSystemClient],
    namespace: NamespaceResource,
) -> List[DataLakeFile]:
    """Fetches all files in the data lake for a given namespace."""
    return fetch_all_files_in_data_lake_no_op(
        context=context,
        data_lake_client=data_lake_client,
        namespace=namespace,
    )
