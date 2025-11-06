import hashlib
import time
from typing import Any

from aihub_lib.persistence.rag.vectors.node_metadata import (
    CREATED_AT,
    DOCUMENT_TITLE,
    HASH,
    INSERTED_AT,
    SOURCE_ORIGIN,
    UPDATED_AT,
)
from dagster import op

from aihub_pipeline.types.SourceFile import SourceFile


@op(code_version="v1")
def extract_metadata_from_source_file(source_file: SourceFile) -> dict[str, Any]:
    """
    Extract metadata from a source file.

    This generic operation works with any source file type (SharePoint, local file system, etc.)
    that implements the SourceFile interface. It generates standardized metadata including
    timestamps, content hash, and source origin.
    """
    metadata: dict[str, Any] = {
        SOURCE_ORIGIN: source_file.source_url,
        INSERTED_AT: int(time.time()),
        UPDATED_AT: int(source_file.modified_datetime.timestamp()),
        CREATED_AT: int(source_file.created_datetime.timestamp()),
        DOCUMENT_TITLE: source_file.name,
        HASH: hashlib.sha256(source_file.content).hexdigest(),
    }
    return metadata
