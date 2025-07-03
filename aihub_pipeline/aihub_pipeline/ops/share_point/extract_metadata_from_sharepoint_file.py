import hashlib
import time
from typing import Any, Dict

from aihub_lib.persistence.rag.vectors.node_metadata import (
    CREATED_AT,
    DOCUMENT_TITLE,
    HASH,
    INSERTED_AT,
    SOURCE,
    UPDATED_AT,
)
from dagster import op

from aihub_pipeline.types.SharePointFile import SharePointFile


@op(code_version="v1")
def extract_metadata_from_share_point_file(sharepoint_file: SharePointFile) -> Dict[str, Any]:
    metadata: Dict[str, Any] = {
        SOURCE: sharepoint_file.full_url,
        INSERTED_AT: int(time.time()),
        UPDATED_AT: int(sharepoint_file.modified_datetime.timestamp()),
        CREATED_AT: int(sharepoint_file.created_datetime.timestamp()),
        DOCUMENT_TITLE: sharepoint_file.name,
        HASH: hashlib.sha256(sharepoint_file.content).hexdigest(),
    }
    return metadata
