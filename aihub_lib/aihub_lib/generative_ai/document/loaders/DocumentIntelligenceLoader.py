import html
import os
from typing import Any

from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeOutputOption, AnalyzeResult, DocumentContentFormat
from azure.core.credentials import AzureKeyCredential
from bs4 import BeautifulSoup
from fsspec import AbstractFileSystem
from llama_index.core.readers.base import BaseReader
from llama_index.core.readers.file.base import get_default_fs
from llama_index.core.schema import Document

from aihub_lib.generative_ai.utils.path_utils import FIGURES_DIRECTORY_NAME, create_figures_folder_name
from aihub_lib.infrastructure.azure_cognitive_services.AzureDocumentIntelligenceSettings import (
    AzureDocumentIntelligenceSettings,
)
from aihub_lib.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn
from aihub_lib.persistence.rag.vectors.node_metadata import (
    NODE_CONTENT_TYPE_FIGURE,
    NUMBER_OF_PAGES,
)

PAGE_BREAK = "<!-- PageBreak -->"


class DocumentIntelligenceLoader(BaseReader):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        settings = AzureDocumentIntelligenceSettings()
        self.document_intelligence_client = DocumentIntelligenceClient(
            endpoint=settings.ENDPOINT,
            credential=AzureKeyCredential(settings.API_KEY.get_secret_value()),
            api_version=settings.API_VERSION,
        )

    @trace_fn
    def load_data(
        self,
        file: str,
        extra_info: dict | None = None,
        fs: AbstractFileSystem | None = None,
        include_images: bool | None = None,
    ) -> list[Document]:
        """Load and process documents synchronously using the Document Intelligence service."""
        include_images = include_images if include_images is not None else True

        fs = fs or get_default_fs()
        with fs.open(file, "rb") as pdf_file:
            output_options = [AnalyzeOutputOption.FIGURES] if include_images else []

            poller = self.document_intelligence_client.begin_analyze_document(
                "prebuilt-layout",
                body=pdf_file,
                content_type="application/octet-stream",
                output_content_format=DocumentContentFormat.MARKDOWN,
                output=output_options,
            )

        result: AnalyzeResult = poller.result()
        return self._process_document_intelligence_response(result, poller, file, extra_info, fs, include_images)

    def _process_document_intelligence_response(
        self,
        result: AnalyzeResult,
        poller: Any,
        file: str,
        extra_info: dict | None = None,
        fs: AbstractFileSystem | None = None,
        include_images: bool | None = None,
    ) -> list[Document]:
        """Process the Document Intelligence API response into Document objects."""
        metadata = {NUMBER_OF_PAGES: len(result.pages)}

        text = result.content

        if not include_images:
            text = remove_figure_tags_keep_content(text)
            return [
                Document(
                    text=text,
                    extra_info={**extra_info, **metadata} if extra_info else metadata,
                )
            ]

        if not FIGURES_DIRECTORY_NAME or not result.figures:
            return [
                Document(
                    text=text,
                    extra_info={**extra_info, **metadata} if extra_info else metadata,
                )
            ]

        operation_id = poller.details["operation_id"]

        soup = BeautifulSoup(text, "html.parser")
        figure_tags = soup.find_all("figure")

        if len(result.figures) != len(figure_tags):
            raise ValueError(
                f"Mismatch between number of figures returned by the API ({len(result.figures)}) "
                f"and number of <figure> tags in the document ({len(figure_tags)})."
            )

        figures_dir = create_figures_folder_name(file)
        for idx, (figure, figure_tag) in enumerate(zip(result.figures, figure_tags)):
            response = self.document_intelligence_client.get_analyze_result_figure(
                model_id="prebuilt-layout",
                result_id=operation_id,
                figure_id=figure.id,
            )

            blob_path = os.path.join(figures_dir, f"figure_{idx + 1}.png")
            with fs.open(blob_path, "wb") as pdf_file:
                for chunk in response:
                    pdf_file.write(chunk)

            markdown_figure = f"![Figure {idx + 1}]({blob_path})"
            figure_tag.replace_with(f"<{NODE_CONTENT_TYPE_FIGURE}>{markdown_figure}</{NODE_CONTENT_TYPE_FIGURE}>")

        return [
            Document(
                text=html.unescape(str(soup)),
                extra_info={**extra_info, **metadata} if extra_info else metadata,
            )
        ]


def remove_figure_tags_keep_content(document_text: str) -> str:
    """Remove figure tags but keep their inner content."""
    soup = BeautifulSoup(document_text, "html.parser")

    figure_tags = soup.find_all("figure")

    for figure_tag in figure_tags:
        inner_content = figure_tag.get_text()
        figure_tag.replace_with(inner_content)

    return html.unescape(str(soup))
