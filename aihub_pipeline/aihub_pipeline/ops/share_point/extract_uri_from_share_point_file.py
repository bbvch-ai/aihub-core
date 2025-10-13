from dagster import op

from aihub_pipeline.resources.data_lake.DataLakeResource import DataLakeResource
from aihub_pipeline.types.SharePointFile import SharePointFile


@op(code_version="v1")
def extract_uri_from_share_point_file(
    share_point_file: SharePointFile,
    data_lake_resource: DataLakeResource,
) -> str:
    parts = [data_lake_resource.container_name]
    if data_lake_resource.directory_name is not None:
        parts.append(data_lake_resource.directory_name)
    parts.append(share_point_file.path.lstrip("/"))
    return "/".join(parts)
