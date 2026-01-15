import hashlib

S3_PROTOCOL_PREFIX = "s3://"


def source_to_doc_id(source_path: str) -> str:
    """Generate deterministic document ID from source path.

    Uses SHA256 hash of the normalized source path, truncated to 24 hex chars
    to fit MongoDB ObjectId format.

    This ensures:
    - Same file always gets the same RefDoc ID
    - Placeholder creation on upload uses predictable ID
    - Upsert/update when processing completes can find the document
    """
    normalized = source_path if source_path.startswith(S3_PROTOCOL_PREFIX) else f"{S3_PROTOCOL_PREFIX}{source_path}"
    hash_hex = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    return hash_hex[:24]
