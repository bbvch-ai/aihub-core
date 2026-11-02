from typing import Annotated

from pydantic import BaseModel, Field, computed_field

from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_content_line import KnowledgeContentLine
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_document_summary import KnowledgeDocumentSummary


class KnowledgeContentMatch(BaseModel):
    """A document whose parsed text matched, with its first matching lines and how many there are in total."""

    summary: Annotated[KnowledgeDocumentSummary, Field(description="The document's listing entry")]
    lines: Annotated[list[KnowledgeContentLine], Field(description="The first matching lines, in text order")]
    matching_line_count: Annotated[int, Field(description="How many lines of the document match")]

    @computed_field
    @property
    def lines_truncated(self) -> bool:
        return self.matching_line_count > len(self.lines)
