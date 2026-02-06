"""
MarkItDown Document Loader.

Uses the MarkItDown library to convert Office documents (DOCX, PPTX, XLSX, etc.)
to markdown format. Handles embedded images by extracting them and uploading
to S3 storage.

This loader is used as a fallback for file types not supported by MinerU.
"""

import asyncio
import logging
import os
import tempfile
from typing import TYPE_CHECKING, Any

from llama_index.core.readers.base import BaseReader
from llama_index.core.readers.file.base import get_default_fs
from llama_index.core.schema import Document

from aihub_lib.generative_ai.document.tables.markdown_table import wrap_tables_with_tags
from aihub_lib.generative_ai.utils.image_processor import (
    embed_images_as_base64,
    extract_and_upload_images,
    extract_base64_images_from_markdown,
)
from aihub_lib.infrastructure.api.AIHubSettings import AIHubSettings
from aihub_lib.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn
from aihub_lib.persistence.rag.vectors.node_metadata import NUMBER_OF_PAGES

if TYPE_CHECKING:
    from fsspec import AbstractFileSystem

logger = logging.getLogger(__name__)


class MarkItDownLoader(BaseReader):
    """
    Document loader using MarkItDown for Office document conversion.

    Converts DOCX, PPTX, XLSX, XLS, and Outlook message files to markdown.
    Handles embedded images by extracting base64 data and uploading to S3.

    ### Supported Extensions
    - docx, pptx, xlsx, xls (Microsoft Office)
    - msg, eml (Outlook messages)

    ### Output Format
    Returns LlamaIndex Documents with:
    - Markdown text content
    - Images wrapped in `<figure>` tags with S3 paths
    - Tables wrapped in `<table>` tags
    """

    SUPPORTED_EXTENSIONS: list[str] = ["docx", "pptx", "xlsx", "xls", "msg", "eml"]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        # Lazy import to avoid loading MarkItDown until needed
        self._converter = None

    def _get_converter(self):
        """Lazy-load the MarkItDown converter."""
        if self._converter is None:
            from markitdown import MarkItDown

            self._converter = MarkItDown()
        return self._converter

    @trace_fn
    def load_data(
        self,
        file: str,
        extra_info: dict | None = None,
        fs: "AbstractFileSystem | None" = None,
        include_images: bool = True,
    ) -> list[Document]:
        """Load and process document synchronously using MarkItDown."""
        return asyncio.run(self.aload_data(file, extra_info, fs, include_images))

    async def aload_data(
        self,
        file: str,
        extra_info: dict | None = None,
        fs: "AbstractFileSystem | None" = None,
        include_images: bool = True,
    ) -> list[Document]:
        """Load and process document asynchronously using MarkItDown."""
        fs = fs or get_default_fs()
        filename = os.path.basename(file)

        logger.debug(f"[MarkItDownLoader] Starting load for file: {filename}")

        # Read file content
        file_bytes = await asyncio.to_thread(fs.cat_file, file)
        logger.debug(f"[MarkItDownLoader] File read complete: {filename}, size: {len(file_bytes)} bytes")

        # Convert using MarkItDown
        md_content = await self._convert_to_markdown(file_bytes, filename)
        logger.debug(f"[MarkItDownLoader] Conversion complete for: {filename}")

        # Process images if included
        if include_images:
            md_content = await self._process_images(md_content, file, fs)

        # Wrap tables in <table> tags
        md_content = self._wrap_tables(md_content)

        # Build metadata
        metadata = {
            NUMBER_OF_PAGES: 1,  # MarkItDown doesn't provide page count
            "parser": "markitdown",
        }

        if extra_info:
            metadata.update(extra_info)

        logger.debug(f"[MarkItDownLoader] Processing complete for: {filename}")

        return [Document(text=md_content, extra_info=metadata)]

    async def aload_data_from_bytes(
        self,
        content: bytes,
        filename: str,
        extra_info: dict | None = None,
        fs: "AbstractFileSystem | None" = None,
        include_images: bool = True,
        embed_base64: bool = False,
    ) -> list[Document]:
        """
        Load and process document from raw bytes.

        Used by the API layer when documents are uploaded directly.

        ### Arguments
        - `content`: Raw bytes of the document
        - `filename`: Name of the file (used for extension detection and output paths)
        - `extra_info`: Additional metadata to include in the Document
        - `fs`: Filesystem for storing extracted images (required unless embed_base64=True)
        - `include_images`: Whether to extract images from the document
        - `embed_base64`: If True, embed images as base64 data URIs instead of uploading to S3

        ### Raises
        - `ValueError`: If `include_images` is True, `embed_base64` is False, and no filesystem is provided
        """
        if include_images and not embed_base64 and fs is None:
            raise ValueError(
                "Filesystem (fs) is required when include_images=True and embed_base64=False. "
                "Provide an S3 filesystem to store extracted images, or set embed_base64=True."
            )

        # Use local filesystem only if images are not being extracted to S3
        if fs is None:
            fs = get_default_fs()

        logger.debug(
            f"[MarkItDownLoader] Processing from bytes: {filename}, {len(content)} bytes, embed_base64={embed_base64}"
        )

        # Convert using MarkItDown
        md_content = await self._convert_to_markdown(content, filename)

        # For API usage, use synthetic path with S3 bucket prefix for figure storage
        bucket_name = AIHubSettings().SHARED_BUCKET_NAME
        synthetic_file = f"{bucket_name}/api_uploads/{filename}"

        # Process images if included
        if include_images:
            md_content = await self._process_images(md_content, synthetic_file, fs, embed_base64)

        # Wrap tables
        md_content = self._wrap_tables(md_content)

        # Build metadata
        metadata = {
            NUMBER_OF_PAGES: 1,
            "parser": "markitdown",
        }

        if extra_info:
            metadata.update(extra_info)

        return [Document(text=md_content, extra_info=metadata)]

    async def _convert_to_markdown(self, file_bytes: bytes, filename: str) -> str:
        """Convert document to markdown using MarkItDown."""
        # MarkItDown requires a file path, so we need to write to a temp file
        ext = os.path.splitext(filename)[1].lower()

        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp_file:
            tmp_file.write(file_bytes)
            tmp_path = tmp_file.name

        try:
            # Run conversion in thread pool (MarkItDown is synchronous)
            result = await asyncio.to_thread(
                self._get_converter().convert,
                tmp_path,
                keep_data_uris=True,  # Keep images as base64 data URIs
            )
            return result.text_content
        finally:
            # Clean up temp file
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    async def _process_images(
        self,
        md_content: str,
        source_file: str,
        fs: "AbstractFileSystem",
        embed_base64: bool = False,
    ) -> str:
        """Extract base64 images and optionally upload to S3 or keep as data URIs."""
        # Extract inline base64 images from markdown
        cleaned_md, images = await extract_base64_images_from_markdown(md_content)

        if not images:
            return md_content

        if embed_base64:
            # Keep images as base64 data URIs, just wrap in <figure> tags
            return embed_images_as_base64(
                markdown_content=cleaned_md,
                images=images,
            )
        else:
            # Upload images to S3 and update references
            return await extract_and_upload_images(
                markdown_content=cleaned_md,
                images=images,
                fs=fs,
                source_file=source_file,
            )

    def _wrap_tables(self, markdown_content: str) -> str:
        """
        Wrap markdown tables in <table> tags for downstream processing.

        Uses pattern matching to find markdown tables and wraps them.
        """
        import re

        # Pattern to match markdown tables
        pattern = r"(\|[^\n]+\|\r?\n\|[:\-| ]+\|\r?(?:\n\|[^\n]+\|\r?)*)"

        tables = re.findall(pattern, markdown_content)

        for table in tables:
            wrapped = wrap_tables_with_tags([table])
            markdown_content = markdown_content.replace(table, wrapped, 1)

        return markdown_content
