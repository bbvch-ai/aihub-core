"""
Image processing utilities for document loaders.

Provides shared functionality for extracting, uploading, and referencing images
from parsed documents. Used by MineruLoader and MarkItDownLoader to ensure
consistent image handling across different parsing backends.

MinerU emits figures as JPEG (mineru/utils/pdf_image_tools.py:cut_image), so we
write the bytes through unchanged — re-encoding a JPEG photograph to PNG would
inflate the payload by an order of magnitude. Per-document dedup via dHash still
collapses repeated logos.

Only raster images become figures: an image of another type (SVG, WMF, EMF), or one that does not decode, is skipped
and its reference replaced with an `[image: <alt>]` marker, so its alt text and the rest of the document are kept.
"""

import asyncio
import base64
import hashlib
import logging
import os
import re
from collections.abc import Callable
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

BASE64_IMAGE_PATTERN = r"!\[([^\]]*)\]\((data:image/[^;]+;base64,[^)]+)\)"

# A figure's folder is named after its document and may contain ")" (e.g. "Report_(1)_docx"), so the reference
# ends at the figure file this module writes (`figure_<hash>.<ext>`), not at the first closing parenthesis.
S3_FIGURE_REFERENCE_PATTERN = r"!\[([^\]]*)\]\((s3://([^/]+)/(.+?/figure_[0-9a-f]+\.[A-Za-z0-9]+))\)"

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
_RASTER_MIME_TO_EXT = {
    "jpeg": "jpg",
    "jpg": "jpg",
    "png": "png",
    "gif": "gif",
    "webp": "webp",
    "bmp": "bmp",
    "tiff": "tiff",
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
    markdown_content, images = _drop_non_raster_images(markdown_content, images, source_file)
    if not images:
        return markdown_content

    figures_dir = create_figures_folder_name(source_file)

    await asyncio.to_thread(fs.makedirs, figures_dir, exist_ok=True)

    seen: list[tuple[imagehash.ImageHash, str]] = []
    figure_number = 0

    for rel_path, data_uri in images.items():
        base64_data, mime_prefix = _split_data_uri(data_uri)
        image_bytes = base64.b64decode(base64_data)

        try:
            image_hash = await asyncio.to_thread(_image_hash, image_bytes)
        except OSError:
            # A raster that is truncated or corrupt is skipped like a non-raster image (#479, #1567).
            logger.warning(f"Skipping image {rel_path} in {source_file}: {mime_prefix or 'raw base64'} does not decode")
            markdown_content = _replace_image_reference(markdown_content, rel_path, _marker_keeping_alt)
            continue

        figure_number += 1
        s3_uri = await _store_figure(fs, figures_dir, rel_path, mime_prefix, image_bytes, image_hash, seen)
        figure_tag = _figure_tag(figure_number, s3_uri)
        markdown_content = _replace_image_reference(markdown_content, rel_path, lambda _, tag=figure_tag: tag)

    return markdown_content


async def _store_figure(
    fs: "AbstractFileSystem",
    figures_dir: str,
    rel_path: str,
    mime_prefix: str,
    image_bytes: bytes,
    image_hash: imagehash.ImageHash,
    seen: list[tuple[imagehash.ImageHash, str]],
) -> str:
    """Write the figure, or reuse an earlier one it perceptually matches, and return its S3 URI."""
    if (existing_uri := _find_perceptual_match(image_hash, seen)) is not None:
        logger.debug(f"Image {rel_path} matches an uploaded figure (hash={image_hash}); reusing {existing_uri}")
        return existing_uri

    extension = _detect_extension(mime_prefix, rel_path, image_bytes)
    content_hash = hashlib.sha256(image_bytes).hexdigest()[:16]
    blob_path = f"{figures_dir}/figure_{content_hash}.{extension}"

    await asyncio.to_thread(_write_file, fs, blob_path, image_bytes)

    s3_uri = blob_path if blob_path.startswith("s3://") else f"s3://{blob_path}"
    seen.append((image_hash, s3_uri))
    logger.debug(f"Uploaded image {rel_path} to {s3_uri} ({len(image_bytes)} bytes)")
    return s3_uri


def _figure_tag(figure_number: int, uri: str) -> str:
    return f"<{NODE_CONTENT_TYPE_FIGURE}>![Figure {figure_number}]({uri})</{NODE_CONTENT_TYPE_FIGURE}>"


def image_marker(alt: str) -> str:
    """The text left where an image is not kept; it carries the alt text, which often describes the image."""
    alt_text = alt.strip()
    return f"[image: {alt_text}]" if alt_text else "[image]"


def _marker_keeping_alt(match: re.Match[str]) -> str:
    return image_marker(match.group(1))


def _replace_image_reference(
    markdown_content: str,
    rel_path: str,
    replacement: Callable[[re.Match[str]], str],
) -> str:
    """Replace every reference to the image in the forms the loaders write (`images/x`, `./images/x`, `x`)."""
    for pattern in (f"images/{rel_path}", f"./images/{rel_path}", rel_path):
        markdown_content = re.sub(rf"!\[([^\]]*)\]\({re.escape(pattern)}\)", replacement, markdown_content)
    return markdown_content


def _is_raster_figure(data_uri: str) -> bool:
    """
    Decided by the MIME type before Pillow sees the bytes: a malformed WMF or EMF makes Pillow raise ValueError or
    ZeroDivisionError, not only OSError. Raw base64 without a MIME type is left to the decode in the upload.
    """
    _, mime_prefix = _split_data_uri(data_uri)
    if not mime_prefix:
        return True
    match = _DATA_URI_MIME_RE.match(mime_prefix + ",")
    return match is not None and match.group(1).lower() in _RASTER_MIME_TO_EXT


def _drop_non_raster_images(
    markdown_content: str,
    images: dict[str, str],
    source: str,
) -> tuple[str, dict[str, str]]:
    """
    Only raster figures are stored or embedded, because every consumer assumes one: the vision model that describes
    figures, the agents that sign them for a model, and the UIs that render them.
    """
    kept: dict[str, str] = {}
    for rel_path, data_uri in images.items():
        if _is_raster_figure(data_uri):
            kept[rel_path] = data_uri
            continue
        _, mime_prefix = _split_data_uri(data_uri)
        logger.warning(f"Skipping image {rel_path} in {source}: {mime_prefix} is not a raster image")
        markdown_content = _replace_image_reference(markdown_content, rel_path, _marker_keeping_alt)
    return markdown_content, kept


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
        if (ext := _RASTER_MIME_TO_EXT.get(mime_subtype)) is not None:
            return ext
    _, file_ext = os.path.splitext(rel_path)
    if (normalised := file_ext.lower().lstrip(".")) in _RASTER_MIME_TO_EXT.values():
        return normalised
    with Image.open(BytesIO(image_bytes)) as img:
        return (img.format or "jpg").lower().replace("jpeg", "jpg")


def _image_hash(image_bytes: bytes) -> imagehash.ImageHash:
    """Perceptual hash robust to sub-pixel crop shifts and rendering artifacts from VLM-driven figure extraction."""
    with Image.open(BytesIO(image_bytes)) as img:
        return imagehash.dhash(img, hash_size=_HASH_SIZE)


def _find_perceptual_match(
    image_hash: imagehash.ImageHash,
    seen: list[tuple[imagehash.ImageHash, str]],
) -> str | None:
    """Linear scan: returns the first stored URI whose hash is within the perceptual-match threshold."""
    for existing_hash, existing_uri in seen:
        if image_hash - existing_hash <= _HASH_MATCH_THRESHOLD:
            return existing_uri
    return None


def embed_images_as_base64(
    markdown_content: str,
    images: dict[str, str],
    source_file: str = "",
) -> str:
    """
    Embed images as base64 data URIs directly in markdown content.

    Takes a dictionary of image paths to base64-encoded data and replaces
    the image references in the markdown content with inline data URIs
    wrapped in <figure> tags. Nothing is decoded, because this runs on the
    event loop: only the MIME type decides which images are kept.
    """
    markdown_content, images = _drop_non_raster_images(markdown_content, images, source_file or "an uploaded document")
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

        figure_tag = _figure_tag(idx + 1, data_uri)
        markdown_content = _replace_image_reference(markdown_content, rel_path, lambda _, tag=figure_tag: tag)

        logger.debug(f"Embedded image {idx + 1} as base64 data URI")

    return markdown_content


def extract_base64_images_from_markdown(markdown_content: str) -> tuple[str, dict[str, str]]:
    """
    Extract base64-encoded images from markdown content.

    Finds all inline base64 images (data URIs) in markdown image syntax
    and returns them as a dictionary for later processing.
    """
    images: dict[str, str] = {}

    def replace_with_placeholder(match: re.Match) -> str:
        alt_text = match.group(1)
        data_uri = match.group(2)

        idx = len(images) + 1
        placeholder = f"inline_image_{idx}.png"
        images[placeholder] = data_uri

        return f"![{alt_text}]({placeholder})"

    cleaned_markdown = re.sub(BASE64_IMAGE_PATTERN, replace_with_placeholder, markdown_content)

    return cleaned_markdown, images


def strip_base64_images_from_markdown(markdown_content: str) -> str:
    """
    Replace inline base64 images with a short marker, for a reader that wants the text without its images.

    One embedded photo is hundreds of thousands of characters that would otherwise crowd out the text in a prompt
    or preview; the marker keeps the alt text, which often describes the image.
    """
    return re.sub(BASE64_IMAGE_PATTERN, _marker_keeping_alt, markdown_content)


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

    def replace_with_signed_url(match: re.Match) -> str:
        alt_text = match.group(1)
        bucket = match.group(3)
        key = match.group(4)

        signed_url = s3_service.generate_sas_url(bucket, key, lifetime_hours=lifetime_hours)
        return f"![{alt_text}]({signed_url})"

    return await asyncio.to_thread(re.sub, S3_FIGURE_REFERENCE_PATTERN, replace_with_signed_url, markdown_content)
