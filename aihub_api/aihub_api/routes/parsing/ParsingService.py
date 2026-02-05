"""
Document parsing service.

Routes documents to the appropriate loader (MinerU or MarkItDown) based on
file type and handles the conversion process.
"""

import logging

from aihub_lib.generative_ai.document.loaders.MarkItDownLoader import MarkItDownLoader
from aihub_lib.generative_ai.document.loaders.MineruLoader import MineruLoader
from aihub_lib.generative_ai.utils.image_processor import replace_s3_paths_with_signed_urls
from aihub_lib.infrastructure.mineru.MineruSettings import MineruSettings
from fastapi import HTTPException

from aihub_api.routes.parsing.dto.DocumentConversionResponse import (
    DocumentConversionMetadata,
    DocumentConversionResponse,
)
from aihub_api.routes.parsing.ParsingMappings import get_extension

logger = logging.getLogger(__name__)


class ParsingService:
    """Service for converting documents to markdown using MinerU or MarkItDown."""

    @staticmethod
    async def convert_from_bytes(
        content: bytes,
        filename: str,
        content_type: str = "",
        generate_signed_urls: bool = True,
    ) -> DocumentConversionResponse:
        """
        Convert a document from raw bytes to markdown.

        Routes to the appropriate loader based on file extension:
        - MinerU: PDF, images (png, jpg, etc.)
        - MarkItDown: Office documents (docx, pptx, xlsx, etc.)

        For API responses, S3 paths are replaced with short-lived signed URLs
        so clients can access embedded images directly.
        """
        logger.info(f"Converting document: {filename} ({len(content)} bytes)")

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
            # Convert document
            documents = await loader.aload_data_from_bytes(
                content=content,
                filename=filename,
                include_images=True,
            )

            if not documents:
                logger.error(f"No documents returned for {filename}")
                raise HTTPException(
                    status_code=500,
                    detail="Document conversion returned no content",
                )

            markdown_content = documents[0].text

            # Replace S3 paths with signed URLs for API responses
            if generate_signed_urls and markdown_content:
                markdown_content = replace_s3_paths_with_signed_urls(
                    markdown_content,
                    lifetime_hours=1,  # 1 hour expiry for API responses
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
