from dagster import op

from swiss_ai_hub.pipeline.types.source_file import SourceFile


@op(code_version="v1")
def extract_content_from_source_file(source_file: SourceFile) -> bytes:
    """
    Extract content from a source file.

    This generic operation works with any source file type (SharePoint, local file system, etc.)
    that implements the SourceFile interface.
    """
    return source_file.content
