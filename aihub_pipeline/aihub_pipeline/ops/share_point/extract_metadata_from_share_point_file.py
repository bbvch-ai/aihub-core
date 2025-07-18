import hashlib
import time
from typing import Any

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
def extract_metadata_from_share_point_file(share_point_file: SharePointFile) -> dict[str, Any]:
    metadata: dict[str, Any] = {
        SOURCE: share_point_file.full_url,
        INSERTED_AT: int(time.time()),
        UPDATED_AT: int(share_point_file.modified_datetime.timestamp()),
        CREATED_AT: int(share_point_file.created_datetime.timestamp()),
        DOCUMENT_TITLE: share_point_file.name,
        HASH: hashlib.sha256(share_point_file.content).hexdigest(),
    }
    return metadata
