import html
import os
from io import StringIO
from typing import Any, Dict, List, Optional

import pandas as pd
from azure.ai.documentintelligence.models import AnalyzeOutputOption, AnalyzeResult, DocumentContentFormat
from bs4 import BeautifulSoup
from fsspec import AbstractFileSystem
from llama_index.core.readers.base import BaseReader
from llama_index.core.readers.file.base import get_default_fs
from llama_index.core.schema import Document

from aihub_lib.generative_ai.utils.path_utils import create_data_lake_figures_folder_name
from aihub_lib.infrastructure.azure.cognitive_services.document_intelligence.DocumentIntelligenceAccess import (
    DocumentIntelligenceAccess,
)
from aihub_lib.persistence.rag.vectors.node_metadata import (
    NODE_CONTENT_TYPE_FIGURE,
    NODE_CONTENT_TYPE_TABLE,
    NUMBER_OF_PAGES,
)

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
        figures_directory_name: Optional[str] = None,
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

        text = reformat_tables(result.content)

        if not figures_directory_name or not result.figures:
            return [
                Document(
                    text=text,
                    extra_info={**extra_info, **metadata} if extra_info else metadata,
                )
            ]

        operation_id = poller.details["operation_id"]

        soup = BeautifulSoup(text, "html.parser")
        figure_tags = soup.find_all("figure")

        figures_dir = create_data_lake_figures_folder_name(file, figures_directory_name)
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


def reformat_tables(document_text: str) -> str:
    """Convert HTML tables in the document to Markdown tables."""

    soup = BeautifulSoup(document_text, "html.parser")

    table_tags = soup.find_all("table")

    for table in table_tags:
        # TODO if table is very long split into smaller tables with copied headers
        markdown_table = pd.read_html(StringIO(str(table)))[0].fillna("").to_markdown()
        table.replace_with(f"<{NODE_CONTENT_TYPE_TABLE}>{markdown_table}</{NODE_CONTENT_TYPE_TABLE}>")

    return html.unescape(str(soup))
