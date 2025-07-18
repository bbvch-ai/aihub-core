from dagster import op

from aihub_pipeline.types.SharePointFile import SharePointFile


@op(code_version="v1")
def extract_content_from_share_point_file(share_point_file: SharePointFile) -> bytes:
    return share_point_file.content
