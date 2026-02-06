"""Image handling mode for parsed documents."""

from enum import StrEnum


class ImageMode(StrEnum):
    """Image handling mode for parsed documents."""

    S3 = "s3"  # Upload to S3, return signed URLs (default)
    BASE64 = "base64"  # Embed images as base64 data URIs in markdown
