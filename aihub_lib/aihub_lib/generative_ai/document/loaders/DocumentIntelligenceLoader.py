from typing import Any, Dict, List, Optional

from azure.ai.documentintelligence.models import AnalyzeResult, DocumentContentFormat
from fsspec import AbstractFileSystem
from llama_index.core.readers.base import BaseReader
from llama_index.core.readers.file.base import get_default_fs
from llama_index.core.schema import Document

from aihub_lib.infrastructure.azure.cognitive_services.document_intelligence.DocumentIntelligenceAccess import (
    DocumentIntelligenceAccess,
)


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
                analyze_request=pdf_file,
                content_type="application/octet-stream",
                output_content_format=DocumentContentFormat.MARKDOWN,
            )
        result: AnalyzeResult = poller.result()
        metadata = {"number_of_pages": len(result.pages)}
        return [
            Document(
                text=result.content,
                extra_info={**extra_info, **metadata} if extra_info else metadata,
            )
        ]
