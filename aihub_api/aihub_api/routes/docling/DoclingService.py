import base64
import logging
from io import BytesIO

from aihub_lib.generative_ai.document.loaders.DoclingLoader import DoclingLoader
from pypdf import PdfReader, PdfWriter
from pypdf.generic import RectangleObject

from aihub_api.routes.docling.dto.DocumentConversionResponse import (
    DocumentConversionMetadata,
    DocumentConversionResponse,
)

logger = logging.getLogger(__name__)


class DoclingService:
    @staticmethod
    def _fix_pdf_mediabox(content: bytes, filename: str) -> bytes:
        """
        Fix PDF files with missing or invalid page dimensions (mediabox).

        Some PDFs have pages without proper mediabox definitions, which causes
        parsing issues. This method reads and rewrites the PDF to ensure all
        pages have valid dimensions.
        """
        if not filename.lower().endswith(".pdf"):
            return content

        try:
            reader = PdfReader(BytesIO(content))
            writer = PdfWriter()

            for page in reader.pages:
                if page.mediabox is None or page.mediabox.width == 0 or page.mediabox.height == 0:
                    # Set default A4 dimensions (595 x 842 pt) if missing
                    page.mediabox = RectangleObject((0, 0, 595, 842))
                writer.add_page(page)

            output = BytesIO()
            writer.write(output)
            return output.getvalue()
        except Exception as e:
            logger.warning(f"Could not preprocess PDF {filename}: {e}")
            return content

    @staticmethod
    async def convert_from_bytes(content: bytes, filename: str) -> DocumentConversionResponse:
        logger.info(f"Converting document: {filename} ({len(content)} bytes)")

        content = DoclingService._fix_pdf_mediabox(content, filename)
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
