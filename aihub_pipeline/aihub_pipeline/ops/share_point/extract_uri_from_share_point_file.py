from dagster import op

from aihub_pipeline.resources.data_lake.DataLakeResource import DataLakeResource
from aihub_pipeline.types.SharePointFile import SharePointFile


@op(code_version="v1")
def extract_uri_from_share_point_file(
    share_point_file: SharePointFile,
    data_lake_resource: DataLakeResource,
) -> str:
    return (
        f"{data_lake_resource.container_name}/{data_lake_resource.directory_name}/{share_point_file.path.lstrip('/')}"
    )
