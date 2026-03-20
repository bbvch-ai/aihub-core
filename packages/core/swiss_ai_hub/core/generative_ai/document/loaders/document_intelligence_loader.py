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

from swiss_ai_hub.core.generative_ai.utils.path_utils import FIGURES_DIRECTORY_NAME, create_figures_folder_name
from swiss_ai_hub.core.infrastructure.azure_cognitive_services.azure_document_intelligence_settings import (
    AzureDocumentIntelligenceSettings,
)
from swiss_ai_hub.core.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn
from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import (
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
        file_bytes = fs.cat_file(file)
        output_options = [AnalyzeOutputOption.FIGURES] if include_images else []

        poller = self.document_intelligence_client.begin_analyze_document(
            "prebuilt-layout",
            body=file_bytes,
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
        figures_dir = create_figures_folder_name(file)

        text = self._replace_figures_by_spans(
            text=text,
            result=result,
            operation_id=operation_id,
            figures_dir=figures_dir,
            fs=fs,
        )

        return [
            Document(
                text=html.unescape(text),
                extra_info={**extra_info, **metadata} if extra_info else metadata,
            )
        ]

    def _replace_figures_by_spans(
        self,
        text: str,
        result: AnalyzeResult,
        operation_id: str,
        figures_dir: str,
        fs: AbstractFileSystem,
    ) -> str:
        """
        Replace figures in text using span offsets from the API response.

        Processes figures in reverse order (by offset) to prevent offset shifts during replacement.
        Figures are numbered sequentially (1, 2, 3...) in document order.

        Note: Only the first span is used if a figure has multiple spans. Figures without spans
        are silently skipped and will not appear in the output.
        """
        if not result.figures:
            return text

        # Sort figures by offset in reverse order
        if any(not fig.spans for fig in result.figures):
            missing_ids = [fig.id for fig in result.figures if not fig.spans]
            raise ValueError(f"Missing span information for figures: {missing_ids}")
        figures_with_spans = [(fig, fig.spans[0].offset, fig.spans[0].length) for fig in result.figures if fig.spans]
        figures_with_spans.sort(key=lambda x: x[1], reverse=True)

        figure_counter = len(figures_with_spans)

        for figure, offset, length in figures_with_spans:
            response = self.document_intelligence_client.get_analyze_result_figure(
                model_id="prebuilt-layout",
                result_id=operation_id,
                figure_id=figure.id,
            )

            blob_path = os.path.join(figures_dir, f"figure_{figure_counter}.png")
            with fs.open(blob_path, "wb") as img_file:
                for chunk in response:
                    img_file.write(chunk)

            markdown_figure = f"![Figure {figure_counter}]({blob_path})"
            replacement = f"<{NODE_CONTENT_TYPE_FIGURE}>{markdown_figure}</{NODE_CONTENT_TYPE_FIGURE}>"
            if offset < 0 or offset + length > len(text):
                raise ValueError(f"Figure span ({offset}, {length}) out of bounds for text length {len(text)}")
            text = text[:offset] + replacement + text[offset + length :]
            figure_counter -= 1

        return text


def remove_figure_tags_keep_content(document_text: str) -> str:
    """Remove figure tags but keep their inner content."""
    soup = BeautifulSoup(document_text, "html.parser")

    figure_tags = soup.find_all("figure")

    for figure_tag in figure_tags:
        inner_content = figure_tag.get_text()
        figure_tag.replace_with(inner_content)

    return html.unescape(str(soup))
