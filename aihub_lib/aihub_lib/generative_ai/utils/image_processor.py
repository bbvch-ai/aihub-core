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

from aihub_lib.generative_ai.utils.path_utils import create_figures_folder_name
from aihub_lib.infrastructure.s3.use_s3 import create_s3_service
from aihub_lib.persistence.rag.vectors.node_metadata import NODE_CONTENT_TYPE_FIGURE

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

    ### Arguments
    - `markdown_content`: The markdown text containing image references
    - `images`: Dictionary mapping relative image paths to base64 data URIs or raw base64
    - `fs`: AbstractFileSystem instance for S3/filesystem operations
    - `source_file`: Original source file path (used to generate figures directory)

    ### Returns
    Updated markdown content with S3 paths and <figure> tags
    """
    if not images:
        return markdown_content

    figures_dir = create_figures_folder_name(source_file)

    # Ensure the figures directory exists
    await asyncio.to_thread(fs.makedirs, figures_dir, exist_ok=True)

    for idx, (rel_path, data_uri) in enumerate(images.items()):
        try:
            # Parse data URI to extract base64 content
            if "," in data_uri:
                # Format: data:image/jpeg;base64,/9j/4AAQ...
                base64_data = data_uri.split(",", 1)[1]
            else:
                # Raw base64 string
                base64_data = data_uri

            image_bytes = base64.b64decode(base64_data)

            # Determine file extension from original path or default to png
            _, ext = os.path.splitext(rel_path)
            if not ext:
                ext = ".png"

            # Create S3 path for the image
            figure_filename = f"figure_{idx + 1}{ext}"
            blob_path = os.path.join(figures_dir, figure_filename)

            # Upload to S3 via fsspec
            await asyncio.to_thread(_write_file, fs, blob_path, image_bytes)

            # Create markdown figure reference with s3:// URI for signed URL generation
            # The path format s3://bucket/key is used by replace_s3_paths_with_signed_urls
            s3_uri = f"s3://{blob_path}"
            markdown_figure = f"![Figure {idx + 1}]({s3_uri})"
            figure_tag = f"<{NODE_CONTENT_TYPE_FIGURE}>{markdown_figure}</{NODE_CONTENT_TYPE_FIGURE}>"

            # Replace original image reference in markdown
            # Handle various reference formats: images/xxx.jpg, ./images/xxx.jpg, etc.
            patterns_to_replace = [
                f"images/{rel_path}",
                f"./images/{rel_path}",
                rel_path,
            ]

            for pattern in patterns_to_replace:
                # Replace markdown image syntax ![...](pattern)
                markdown_content = re.sub(
                    rf"!\[[^\]]*\]\({re.escape(pattern)}\)",
                    figure_tag,
                    markdown_content,
                )

            logger.debug(f"Uploaded image {idx + 1} to {s3_uri}")

        except Exception as e:
            # Fail fast - don't silently skip images
            raise RuntimeError(f"Failed to process image {rel_path}: {e}") from e

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

    ### Arguments
    - `markdown_content`: The markdown text containing image references
    - `images`: Dictionary mapping relative image paths to base64 data URIs or raw base64

    ### Returns
    Updated markdown content with embedded base64 images and <figure> tags
    """
    if not images:
        return markdown_content

    for idx, (rel_path, data_uri) in enumerate(images.items()):
        try:
            # Ensure proper data URI format
            if not data_uri.startswith("data:"):
                # Determine mime type from path extension
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

            # Create markdown figure reference with <figure> tag
            markdown_figure = f"![Figure {idx + 1}]({data_uri})"
            figure_tag = f"<{NODE_CONTENT_TYPE_FIGURE}>{markdown_figure}</{NODE_CONTENT_TYPE_FIGURE}>"

            # Replace original image reference in markdown
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

        except Exception as e:
            # Fail fast - don't silently skip images
            raise RuntimeError(f"Failed to embed image {rel_path}: {e}") from e

    return markdown_content


async def extract_base64_images_from_markdown(markdown_content: str) -> tuple[str, dict[str, str]]:
    """
    Extract base64-encoded images from markdown content.

    Finds all inline base64 images (data URIs) in markdown image syntax
    and returns them as a dictionary for later processing.

    ### Arguments
    - `markdown_content`: Markdown text potentially containing inline base64 images

    ### Returns
    Tuple of (cleaned_markdown, images_dict) where:
    - cleaned_markdown: Markdown with base64 data replaced by placeholder paths
    - images_dict: Dictionary mapping placeholder paths to base64 data
    """
    images: dict[str, str] = {}

    # Pattern to match markdown images with data URIs
    # ![alt](data:image/...;base64,...)
    pattern = r"!\[([^\]]*)\]\((data:image/[^;]+;base64,[^)]+)\)"

    def replace_with_placeholder(match: re.Match) -> str:
        alt_text = match.group(1)
        data_uri = match.group(2)

        # Generate a unique placeholder path
        idx = len(images) + 1
        placeholder = f"inline_image_{idx}.png"
        images[placeholder] = data_uri

        return f"![{alt_text}]({placeholder})"

    cleaned_markdown = re.sub(pattern, replace_with_placeholder, markdown_content)

    return cleaned_markdown, images


def replace_s3_paths_with_signed_urls(markdown_content: str, lifetime_hours: int = 1) -> str:
    """
    Replace S3 paths in markdown with short-lived signed URLs.

    Used for API responses where the client needs direct access to images
    without S3 credentials. The signed URLs expire after the specified lifetime.

    ### Arguments
    - `markdown_content`: Markdown text containing S3 paths (s3://bucket/path)
    - `lifetime_hours`: URL expiration time in hours (default: 1 hour)

    ### Returns
    Markdown content with S3 paths replaced by signed URLs
    """
    # Pattern to match S3 paths in markdown images: ![...](s3://bucket/path)
    pattern = r"!\[([^\]]*)\]\((s3://([^/]+)/([^)]+))\)"

    s3_service = create_s3_service()

    def replace_with_signed_url(match: re.Match) -> str:
        alt_text = match.group(1)
        bucket = match.group(3)
        key = match.group(4)

        # Let errors propagate - fail fast instead of silently returning original paths
        signed_url = s3_service.generate_sas_url(bucket, key, lifetime_hours=lifetime_hours)
        return f"![{alt_text}]({signed_url})"

    return re.sub(pattern, replace_with_signed_url, markdown_content)


def wrap_images_in_figure_tags(markdown_content: str) -> str:
    """
    Wrap standalone markdown images in <figure> tags.

    Finds images that are not already wrapped in <figure> tags and wraps them.
    This ensures consistent handling by downstream processors like
    MarkdownStructuralNodeParser.

    ### Arguments
    - `markdown_content`: Markdown text with image references

    ### Returns
    Markdown content with images wrapped in <figure> tags
    """
    # Pattern to match markdown images NOT already in figure tags
    # Negative lookbehind for <figure> and negative lookahead for </figure>
    pattern = r"(?<!<figure>)(!\[[^\]]*\]\([^)]+\))(?!</figure>)"

    def wrap_in_figure(match: re.Match) -> str:
        image_markdown = match.group(1)
        return f"<{NODE_CONTENT_TYPE_FIGURE}>{image_markdown}</{NODE_CONTENT_TYPE_FIGURE}>"

    return re.sub(pattern, wrap_in_figure, markdown_content)
