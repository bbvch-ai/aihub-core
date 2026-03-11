import asyncio
import logging
import mimetypes
import urllib.parse

from fastapi import HTTPException
from swiss_ai_hub.core.generative_ai.document.accessor.s3_anonymous_file_access_service import (
    S3AnonymousFileAccessService,
)
from swiss_ai_hub.core.generative_ai.document.loaders.mark_it_down_loader import MarkItDownLoader
from swiss_ai_hub.core.generative_ai.document.loaders.mineru_loader import MineruLoader
from swiss_ai_hub.core.generative_ai.document.loaders.raw_loader import RawLoader
from swiss_ai_hub.core.generative_ai.utils.image_processor import replace_s3_paths_with_signed_urls
from swiss_ai_hub.core.infrastructure import MineruSettings
from swiss_ai_hub.core.infrastructure import ParsingSettings
from swiss_ai_hub.core.infrastructure import create_s3_filesystem

from swiss_ai_hub.api.routes.parsing.dto.document_parsing_response import (
    DocumentParsingMetadata,
    DocumentParsingResponse,
)
from swiss_ai_hub.api.routes.parsing.dto.image_mode import ImageMode

logger = logging.getLogger(__name__)

_mineru_settings = MineruSettings()
_parsing_settings = ParsingSettings()


def _get_extension(filename: str, content_type: str = "") -> str:
    """Extract file extension from filename or infer from content type via mimetypes."""
    if "." in filename:
        ext = filename.rsplit(".", 1)[-1].lower()
        if ext:
            return ext

    if content_type:
        guessed = mimetypes.guess_extension(content_type, strict=False)
        if guessed:
            return guessed.lstrip(".")

    raise HTTPException(
        status_code=400,
        detail=f"Cannot determine file extension for '{filename}' (content_type='{content_type}')",
    )


class ParsingService:
    """Service for converting documents to markdown using MinerU, MarkItDown, or RawLoader."""

    @staticmethod
    async def convert_from_bytes(
        content: bytes,
        filename: str,
        content_type: str = "",
        image_mode: ImageMode | None = None,
        s3_service: S3AnonymousFileAccessService | None = None,
    ) -> DocumentParsingResponse:
        """
        Convert a document from raw bytes to markdown.

        Routes to the appropriate loader based on file extension:
        - RawLoader: Plaintext files (txt, md, csv, json, xml, yaml, etc.)
        - MinerU: PDF, images (png, jpg, etc.)
        - MarkItDown: Office documents (docx, pptx, xlsx, etc.)
        """
        if image_mode is None:
            image_mode = ImageMode.S3

        if not content:
            raise HTTPException(status_code=400, detail="Request body is empty")

        filename = urllib.parse.unquote(filename)
        content_type = content_type.split(";")[0].strip()

        logger.info(f"Converting document: {filename} ({len(content)} bytes), image_mode={image_mode}")

        extension = _get_extension(filename, content_type)
        if "." not in filename:
            filename = f"{filename}.{extension}"
        logger.debug(f"Detected extension: {extension} for {filename}")

        mineru_extensions = _mineru_settings.EXTENSIONS
        markitdown_extensions = MarkItDownLoader.SUPPORTED_EXTENSIONS
        rawloader_extensions = RawLoader.SUPPORTED_EXTENSIONS

        if extension in rawloader_extensions:
            loader = RawLoader()
            logger.debug(f"Using RawLoader for {filename}")
        elif extension in mineru_extensions:
            loader = MineruLoader()
            logger.debug(f"Using MineruLoader for {filename}")
        elif extension in markitdown_extensions:
            loader = MarkItDownLoader()
            logger.debug(f"Using MarkItDownLoader for {filename}")
        elif extension in _parsing_settings.PASSTHROUGH_EXTENSIONS:
            # OpenWebUI routes ALL uploaded files through the external document loader.
            # Files meant for agent-only processing (e.g. zip, wav) would fail with 400
            # without this passthrough — returning empty content lets the upload succeed
            # while agents access the raw file via S3.
            logger.info(f"Passthrough extension .{extension}, returning empty content: {filename}")
            return DocumentParsingResponse(
                page_content="",
                metadata=DocumentParsingMetadata(filename=filename),
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {extension}. "
                f"Supported types: {', '.join(rawloader_extensions + mineru_extensions + markitdown_extensions)}",
            )

        if image_mode == ImageMode.S3:
            s3_fs = await asyncio.to_thread(create_s3_filesystem)
            documents = await loader.aload_data_from_bytes(
                content=content,
                filename=filename,
                fs=s3_fs,
                include_images=True,
                embed_base64=False,
            )
        else:
            documents = await loader.aload_data_from_bytes(
                content=content,
                filename=filename,
                include_images=True,
                embed_base64=True,
            )

        if not documents:
            raise HTTPException(
                status_code=500,
                detail="Document conversion returned no content",
            )

        markdown_content = documents[0].text

        if image_mode == ImageMode.S3 and markdown_content and s3_service:
            markdown_content = await replace_s3_paths_with_signed_urls(
                markdown_content,
                s3_service=s3_service,
                lifetime_hours=168,
            )

        logger.info(f"Document converted: {filename}, {len(markdown_content)} chars")

        return DocumentParsingResponse(
            page_content=markdown_content,
            metadata=DocumentParsingMetadata(
                filename=filename,
            ),
        )
