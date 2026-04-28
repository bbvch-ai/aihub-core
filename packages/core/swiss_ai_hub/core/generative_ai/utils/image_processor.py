"""
Image processing utilities for document loaders.

Provides shared functionality for extracting, uploading, and referencing images
from parsed documents. Used by MineruLoader and MarkItDownLoader to ensure
consistent image handling across different parsing backends.

MinerU emits figures as JPEG (mineru/utils/pdf_image_tools.py:cut_image), so we
write the bytes through unchanged — re-encoding a JPEG photograph to PNG would
inflate the payload by an order of magnitude. Per-document dedup via dHash still
collapses repeated logos.
"""

import asyncio
import base64
import hashlib
import logging
import os
import re
from io import BytesIO
from typing import TYPE_CHECKING

import imagehash
from PIL import Image

from swiss_ai_hub.core.generative_ai.document.accessor.s3_anonymous_file_access_service import (
    S3AnonymousFileAccessService,
)
from swiss_ai_hub.core.generative_ai.utils.path_utils import create_figures_folder_name
from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import NODE_CONTENT_TYPE_FIGURE

if TYPE_CHECKING:
    from fsspec import AbstractFileSystem

logger = logging.getLogger(__name__)

# dHash on a downscaled image is translation-tolerant: it encodes neighbor-pixel
# gradients, which barely shift when the crop bounds move a few pixels. pHash was
# evaluated and rejected — high-frequency DCT coefficients flip dramatically on
# vertical jitter (74-bit jumps for 2px shifts), making it impossible to set a
# threshold that catches re-cropped logos without merging unrelated figures.
# With hash_size=8 (64-bit fingerprint), measured distances:
#   - same logo, different crop offsets / sub-pixel rescaling: ≤10 bits
#   - genuinely distinct figures: ≥25 bits
# A threshold of 12 sits in the gap and tolerates realistic VLM crop variance.
_HASH_SIZE = 8
_HASH_MATCH_THRESHOLD = 12

_DATA_URI_MIME_RE = re.compile(r"^data:image/([a-zA-Z0-9.+-]+)(?:;[^,]*)?,")
_MIME_TO_EXT = {
    "jpeg": "jpg",
    "jpg": "jpg",
    "png": "png",
    "gif": "gif",
    "webp": "webp",
    "bmp": "bmp",
    "tiff": "tiff",
    "svg+xml": "svg",
}


async def extract_and_upload_images(
    markdown_content: str,
    images: dict[str, str],
    fs: "AbstractFileSystem",
    source_file: str,
) -> str:
    """
    Extract images from a response, upload to S3, and update markdown references.

    Takes a dictionary of image paths to base64-encoded data, uploads each image
    to S3 using fsspec, and replaces the image references in the markdown content
    with the S3 paths wrapped in <figure> tags. Filenames are content-addressed
    (sha256 prefix) so re-runs are idempotent and bytewise duplicates collapse
    naturally; perceptual dedup still catches near-duplicates with different bytes.
    """
    if not images:
        return markdown_content

    figures_dir = create_figures_folder_name(source_file)

    await asyncio.to_thread(fs.makedirs, figures_dir, exist_ok=True)

    seen: list[tuple[imagehash.ImageHash, str]] = []

    for idx, (rel_path, data_uri) in enumerate(images.items()):
        base64_data, mime_prefix = _split_data_uri(data_uri)
        image_bytes = base64.b64decode(base64_data)

        dhash = await asyncio.to_thread(_perceptual_hash, image_bytes)

        if (existing_uri := _find_perceptual_match(dhash, seen)) is not None:
            s3_uri = existing_uri
            logger.debug(f"Image {idx + 1} matches a previously uploaded figure (dHash={dhash}); reusing {s3_uri}")
        else:
            extension = _detect_extension(mime_prefix, rel_path, image_bytes)
            content_hash = hashlib.sha256(image_bytes).hexdigest()[:16]
            blob_path = f"{figures_dir}/figure_{content_hash}.{extension}"

            await asyncio.to_thread(_write_file, fs, blob_path, image_bytes)

            s3_uri = blob_path if blob_path.startswith("s3://") else f"s3://{blob_path}"
            seen.append((dhash, s3_uri))
            logger.debug(f"Uploaded image {idx + 1} to {s3_uri} ({len(image_bytes)} bytes)")

        markdown_figure = f"![Figure {idx + 1}]({s3_uri})"
        figure_tag = f"<{NODE_CONTENT_TYPE_FIGURE}>{markdown_figure}</{NODE_CONTENT_TYPE_FIGURE}>"

        patterns_to_replace = [
            f"images/{rel_path}",
            f"./images/{rel_path}",
            rel_path,
        ]

        for pattern in patterns_to_replace:
            markdown_content = re.sub(
                rf"!\[[^\]]*\]\({re.escape(pattern)}\)",
                figure_tag,
                markdown_content,
            )

    return markdown_content


def _write_file(fs: "AbstractFileSystem", path: str, content: bytes) -> None:
    """Write content to a file using fsspec (synchronous helper for asyncio.to_thread)."""
    with fs.open(path, "wb") as f:
        f.write(content)


def _split_data_uri(data_uri: str) -> tuple[str, str]:
    """Return (base64_payload, mime_prefix). mime_prefix is empty for raw base64 input."""
    if "," in data_uri and data_uri.startswith("data:"):
        prefix, payload = data_uri.split(",", 1)
        return payload, prefix
    if "," in data_uri:
        return data_uri.split(",", 1)[1], ""
    return data_uri, ""


def _detect_extension(mime_prefix: str, rel_path: str, image_bytes: bytes) -> str:
    """Pick the on-disk extension from the data URI MIME, then the source filename, then PIL sniffing."""
    if (match := _DATA_URI_MIME_RE.match(mime_prefix + ",")) is not None:
        mime_subtype = match.group(1).lower()
        if (ext := _MIME_TO_EXT.get(mime_subtype)) is not None:
            return ext
    _, file_ext = os.path.splitext(rel_path)
    if (normalised := file_ext.lower().lstrip(".")) in _MIME_TO_EXT.values():
        return normalised
    with Image.open(BytesIO(image_bytes)) as img:
        return (img.format or "jpg").lower().replace("jpeg", "jpg")


def _perceptual_hash(image_bytes: bytes) -> imagehash.ImageHash:
    """Perceptual hash robust to sub-pixel crop shifts and rendering artifacts from VLM-driven figure extraction."""
    with Image.open(BytesIO(image_bytes)) as img:
        return imagehash.dhash(img, hash_size=_HASH_SIZE)


def _find_perceptual_match(
    dhash: imagehash.ImageHash,
    seen: list[tuple[imagehash.ImageHash, str]],
) -> str | None:
    """Linear scan: returns the first stored URI whose hash is within the perceptual-match threshold."""
    for existing_dhash, existing_uri in seen:
        if dhash - existing_dhash <= _HASH_MATCH_THRESHOLD:
            return existing_uri
    return None


def embed_images_as_base64(
    markdown_content: str,
    images: dict[str, str],
) -> str:
    """
    Embed images as base64 data URIs directly in markdown content.

    Takes a dictionary of image paths to base64-encoded data and replaces
    the image references in the markdown content with inline data URIs
    wrapped in <figure> tags.
    """
    if not images:
        return markdown_content

    for idx, (rel_path, data_uri) in enumerate(images.items()):
        if not data_uri.startswith("data:"):
            _, ext = os.path.splitext(rel_path)
            ext = ext.lower().lstrip(".")
            mime_map = {
                "jpg": "image/jpeg",
                "jpeg": "image/jpeg",
                "png": "image/png",
                "gif": "image/gif",
                "webp": "image/webp",
                "bmp": "image/bmp",
                "tiff": "image/tiff",
            }
            mime_type = mime_map.get(ext, "image/png")
            data_uri = f"data:{mime_type};base64,{data_uri}"

        markdown_figure = f"![Figure {idx + 1}]({data_uri})"
        figure_tag = f"<{NODE_CONTENT_TYPE_FIGURE}>{markdown_figure}</{NODE_CONTENT_TYPE_FIGURE}>"

        patterns_to_replace = [
            f"images/{rel_path}",
            f"./images/{rel_path}",
            rel_path,
        ]

        for pattern in patterns_to_replace:
            markdown_content = re.sub(
                rf"!\[[^\]]*\]\({re.escape(pattern)}\)",
                figure_tag,
                markdown_content,
            )

        logger.debug(f"Embedded image {idx + 1} as base64 data URI")

    return markdown_content


def extract_base64_images_from_markdown(markdown_content: str) -> tuple[str, dict[str, str]]:
    """
    Extract base64-encoded images from markdown content.

    Finds all inline base64 images (data URIs) in markdown image syntax
    and returns them as a dictionary for later processing.
    """
    images: dict[str, str] = {}

    pattern = r"!\[([^\]]*)\]\((data:image/[^;]+;base64,[^)]+)\)"

    def replace_with_placeholder(match: re.Match) -> str:
        alt_text = match.group(1)
        data_uri = match.group(2)

        idx = len(images) + 1
        placeholder = f"inline_image_{idx}.png"
        images[placeholder] = data_uri

        return f"![{alt_text}]({placeholder})"

    cleaned_markdown = re.sub(pattern, replace_with_placeholder, markdown_content)

    return cleaned_markdown, images


async def replace_s3_paths_with_signed_urls(
    markdown_content: str,
    s3_service: S3AnonymousFileAccessService,
    lifetime_hours: int = 1,
) -> str:
    """
    Replace S3 paths in markdown with short-lived signed URLs.

    Used for API responses where the client needs direct access to images
    without S3 credentials. The signed URLs expire after the specified lifetime.
    """
    pattern = r"!\[([^\]]*)\]\((s3://([^/]+)/([^)]+))\)"

    def replace_with_signed_url(match: re.Match) -> str:
        alt_text = match.group(1)
        bucket = match.group(3)
        key = match.group(4)

        signed_url = s3_service.generate_sas_url(bucket, key, lifetime_hours=lifetime_hours)
        return f"![{alt_text}]({signed_url})"

    return await asyncio.to_thread(re.sub, pattern, replace_with_signed_url, markdown_content)
