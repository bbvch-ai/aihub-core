import base64
import logging

from aihub_lib.generative_ai.document.loaders.DoclingLoader import DoclingLoader, _fix_pdf_mediabox

from aihub_api.routes.docling.dto.DocumentConversionResponse import (
    DocumentConversionMetadata,
    DocumentConversionResponse,
)

logger = logging.getLogger(__name__)


class DoclingService:
    @staticmethod
    async def convert_from_bytes(content: bytes, filename: str) -> DocumentConversionResponse:
        logger.info(f"Converting document: {filename} ({len(content)} bytes)")

        content = _fix_pdf_mediabox(content, filename)
        file_content = base64.b64encode(content).decode("utf-8")

        loader = DoclingLoader()
        result = await loader.convert_document_async(
            file_content=file_content,
            filename=filename,
            include_images=True,
            to_formats=["md"],
        )

        logger.info(f"Docling response keys: {result.keys() if result else 'None'}")

        if not result or "document" not in result:
            logger.error(f"Invalid Docling response: {result}")
            raise ValueError("Invalid response from Docling service")

        document = result["document"]
        logger.info(f"Document keys: {document.keys()}")

        markdown_content = document.get("md_content")
        if not markdown_content:
            logger.error(f"No md_content in response: {document.keys()}")
            raise ValueError("No md_content in Docling response")

        logger.info(f"Document converted: {len(markdown_content)} chars")

        return DocumentConversionResponse(
            page_content=markdown_content,
            metadata=DocumentConversionMetadata(filename=filename),
        )
