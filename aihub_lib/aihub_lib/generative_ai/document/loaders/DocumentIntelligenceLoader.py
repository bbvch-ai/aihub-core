import base64
from typing import Any, Dict, List, Optional

from azure.ai.documentintelligence.models import AnalyzeOutputOption, AnalyzeResult, DocumentContentFormat
from bs4 import BeautifulSoup
from fsspec import AbstractFileSystem
from llama_index.core.readers.base import BaseReader
from llama_index.core.readers.file.base import get_default_fs
from llama_index.core.schema import Document

from aihub_lib.infrastructure.azure.cognitive_services.document_intelligence.DocumentIntelligenceAccess import (
    DocumentIntelligenceAccess,
)
from aihub_lib.persistence.rag.vectors.node_metadata import NUMBER_OF_PAGES, NODE_CONTENT_TYPE_FIGURE

PAGE_BREAK = "<!-- PageBreak -->"


class DocumentIntelligenceLoader(BaseReader):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self.document_intelligence_client = DocumentIntelligenceAccess().get_client()

    def load_data(
        self,
        file: str,
        extra_info: Optional[Dict] = None,
        fs: Optional[AbstractFileSystem] = None,
        resource=None,
    ) -> List[Document]:
        fs = fs or get_default_fs()
        with fs.open(file, "rb") as pdf_file:
            poller = self.document_intelligence_client.begin_analyze_document(
                "prebuilt-layout",
                body=pdf_file,
                content_type="application/octet-stream",
                output_content_format=DocumentContentFormat.MARKDOWN,
                output=[AnalyzeOutputOption.FIGURES],
            )

        result: AnalyzeResult = poller.result()

        metadata = {NUMBER_OF_PAGES: len(result.pages)}

        if not result.figures:
            return [
                Document(
                    text=result.content,
                    extra_info={**extra_info, **metadata} if extra_info else metadata,
                )
            ]

        operation_id = poller.details["operation_id"]
        markdown_figures = []
        for idx, figure in enumerate(result.figures):
            response = self.document_intelligence_client.get_analyze_result_figure(
                model_id="prebuilt-layout",
                result_id=operation_id,
                figure_id=figure.id,
            )

            figure_bytes = bytes()
            for chunk in response:
                figure_bytes += chunk
            figure_bytes = base64.b64encode(figure_bytes).decode("utf-8")
            figure_str = f"data:image/png;base64,{figure_bytes}"
            markdown_figure = f"![Figure {idx + 1}]({figure_str})"
            markdown_figures.append(markdown_figure)

        soup = BeautifulSoup(result.content, "html.parser")
        figure_tags = soup.find_all("figure")

        for i, (figure_tag, markdown_figure) in enumerate(zip(figure_tags, markdown_figures)):
            figure_tag.replace_with(f"<{NODE_CONTENT_TYPE_FIGURE}>{markdown_figure}</{NODE_CONTENT_TYPE_FIGURE}>")

        return [
            Document(
                text=str(soup),
                extra_info={**extra_info, **metadata} if extra_info else metadata,
            )
        ]
