"""
Image processing utilities for document loaders.

Provides shared functionality for extracting, uploading, and referencing images
from parsed documents. Used by MineruLoader and MarkItDownLoader to ensure
consistent image handling across different parsing backends.
"""

import asyncio
import base64
import logging
import os
import re
from typing import TYPE_CHECKING

from swiss_ai_hub.core.generative_ai.document.accessor.s3_anonymous_file_access_service import (
    S3AnonymousFileAccessService,
)
from swiss_ai_hub.core.generative_ai.utils.path_utils import create_figures_folder_name
from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import NODE_CONTENT_TYPE_FIGURE

if TYPE_CHECKING:
    from fsspec import AbstractFileSystem

logger = logging.getLogger(__name__)


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
    with the S3 paths wrapped in <figure> tags.
    """
    if not images:
        return markdown_content

    figures_dir = create_figures_folder_name(source_file)

    await asyncio.to_thread(fs.makedirs, figures_dir, exist_ok=True)

    for idx, (rel_path, data_uri) in enumerate(images.items()):
        if "," in data_uri:
            base64_data = data_uri.split(",", 1)[1]
        else:
            base64_data = data_uri

        image_bytes = base64.b64decode(base64_data)

        _, ext = os.path.splitext(rel_path)
        if not ext:
            ext = ".png"

        figure_filename = f"figure_{idx + 1}{ext}"
        blob_path = f"{figures_dir}/{figure_filename}"

        await asyncio.to_thread(_write_file, fs, blob_path, image_bytes)

        # s3://bucket/key format is consumed by replace_s3_paths_with_signed_urls
        s3_uri = blob_path if blob_path.startswith("s3://") else f"s3://{blob_path}"
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

        logger.debug(f"Uploaded image {idx + 1} to {s3_uri}")

    return markdown_content


def _write_file(fs: "AbstractFileSystem", path: str, content: bytes) -> None:
    """Write content to a file using fsspec (synchronous helper for asyncio.to_thread)."""
    with fs.open(path, "wb") as f:
        f.write(content)


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
