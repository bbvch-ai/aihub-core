import hashlib
import time
from typing import Any

from dagster import op
from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import (
    CREATED_AT,
    DOCUMENT_TITLE,
    HASH,
    INSERTED_AT,
    SOURCE_ORIGIN,
    UPDATED_AT,
)

from swiss_ai_hub.pipeline.types.source_file import SourceFile


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
        UPDATED_AT: source_file.modified,
        CREATED_AT: source_file.created,
        DOCUMENT_TITLE: source_file.name,
        HASH: hashlib.sha256(source_file.content).hexdigest(),
    }
    return metadata
