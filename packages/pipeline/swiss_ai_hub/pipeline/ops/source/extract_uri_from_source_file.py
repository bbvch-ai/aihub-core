from dagster import op

from swiss_ai_hub.pipeline.resources.data_lake.DataLakeResource import DataLakeResource
from swiss_ai_hub.pipeline.types.SourceFile import SourceFile


@op(code_version="v1")
def extract_uri_from_source_file(
    source_file: SourceFile,
    data_lake_resource: DataLakeResource,
) -> str:
    """
    Extract and construct the data lake URI for a source file.

    This generic operation works with any source file type (SharePoint, local file system, etc.)
    that implements the SourceFile interface. It constructs the target URI path within the
    data lake based on the configured container, directory, and the file's relative path.
    """
    parts = [data_lake_resource.container_name]
    if data_lake_resource.directory_name is not None:
        parts.append(data_lake_resource.directory_name)
    parts.append(source_file.path.lstrip("/"))
    return "/".join(parts)
