"""
Document parsing service.

Routes documents to the appropriate loader (MinerU or MarkItDown) based on
file type and handles the conversion process.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from aihub_lib.generative_ai.document.loaders.MarkItDownLoader import MarkItDownLoader
from aihub_lib.generative_ai.document.loaders.MineruLoader import MineruLoader
from aihub_lib.generative_ai.utils.image_processor import replace_s3_paths_with_signed_urls
from aihub_lib.infrastructure.mineru.MineruSettings import MineruSettings
from aihub_lib.infrastructure.s3.use_s3 import create_s3_filesystem
from fastapi import HTTPException

from aihub_api.routes.parsing.dto.DocumentConversionResponse import (
    DocumentConversionMetadata,
    DocumentConversionResponse,
)
from aihub_api.routes.parsing.ParsingMappings import get_extension

if TYPE_CHECKING:
    from aihub_api.routes.parsing.ParsingController import ImageMode

logger = logging.getLogger(__name__)


class ParsingService:
    """Service for converting documents to markdown using MinerU or MarkItDown."""

    @staticmethod
    async def convert_from_bytes(
        content: bytes,
        filename: str,
        content_type: str = "",
        image_mode: "ImageMode | None" = None,
    ) -> DocumentConversionResponse:
        """
        Convert a document from raw bytes to markdown.

        Routes to the appropriate loader based on file extension:
        - MinerU: PDF, images (png, jpg, etc.)
        - MarkItDown: Office documents (docx, pptx, xlsx, etc.)

        ### Arguments
        - `content`: Raw bytes of the document
        - `filename`: Original filename (used for extension detection)
        - `content_type`: MIME type of the document
        - `image_mode`: How to handle images - 's3' (default) or 'base64'
        """
        # Import here to avoid circular import
        from aihub_api.routes.parsing.ParsingController import ImageMode

        if image_mode is None:
            image_mode = ImageMode.S3

        logger.info(f"Converting document: {filename} ({len(content)} bytes), image_mode={image_mode}")

        # Determine file extension
        extension = get_extension(filename, content_type)
        logger.debug(f"Detected extension: {extension} for {filename}")

        # Route to appropriate loader
        mineru_extensions = MineruSettings().EXTENSIONS
        markitdown_extensions = MarkItDownLoader.SUPPORTED_EXTENSIONS

        if extension in mineru_extensions:
            loader = MineruLoader()
            logger.debug(f"Using MineruLoader for {filename}")
        elif extension in markitdown_extensions:
            loader = MarkItDownLoader()
            logger.debug(f"Using MarkItDownLoader for {filename}")
        else:
            logger.error(f"Unsupported file type: {extension} for {filename}")
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {extension}. "
                f"Supported types: {', '.join(mineru_extensions + markitdown_extensions)}",
            )

        try:
            if image_mode == ImageMode.S3:
                # S3 mode: Upload images to S3 and return signed URLs
                s3_fs = create_s3_filesystem()
                documents = await loader.aload_data_from_bytes(
                    content=content,
                    filename=filename,
                    fs=s3_fs,
                    include_images=True,
                    embed_base64=False,
                )
            else:
                # Base64 mode: Embed images as data URIs in markdown
                documents = await loader.aload_data_from_bytes(
                    content=content,
                    filename=filename,
                    include_images=True,
                    embed_base64=True,
                )

            if not documents:
                logger.error(f"No documents returned for {filename}")
                raise HTTPException(
                    status_code=500,
                    detail="Document conversion returned no content",
                )

            markdown_content = documents[0].text

            # Replace S3 paths with signed URLs for S3 mode
            if image_mode == ImageMode.S3 and markdown_content:
                markdown_content = replace_s3_paths_with_signed_urls(
                    markdown_content,
                    lifetime_hours=24 * 30,  # 30 days expiry for uploaded files
                )

            logger.info(f"Document converted: {filename}, {len(markdown_content)} chars")

            return DocumentConversionResponse(
                page_content=markdown_content,
                metadata=DocumentConversionMetadata(
                    source=filename,
                    filename=filename,
                ),
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error converting document {filename}: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Error processing document: {type(e).__name__}",
            )
