from typing import Any, Dict, List, Optional

from azure.ai.documentintelligence.models import (
    AnalyzeOutputOption,
    AnalyzeResult,
    DocumentContentFormat,
)
from fsspec import AbstractFileSystem
from llama_index.core.readers.base import BaseReader
from llama_index.core.readers.file.base import get_default_fs
from llama_index.core.schema import Document

from aihub_lib.infrastructure.azure.cognitive_services.document_intelligence.DocumentIntelligenceAccess import (
    DocumentIntelligenceAccess,
)
from aihub_lib.persistence.rag.vectors.node_metadata import NUMBER_OF_PAGES

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
        operation_id = poller.details["operation_id"]
        metadata = {
            NUMBER_OF_PAGES: len(result.pages),
            "operation_id": operation_id,
        }

        if result.figures:
            figure_ids = [figure.id for figure in result.figures]

            metadata.update({"figure_ids": figure_ids})

        return [
            Document(
                text=result.content,
                extra_info={**extra_info, **metadata} if extra_info else metadata,
            )
        ]
