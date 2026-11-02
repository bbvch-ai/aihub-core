from typing import Annotated

from pydantic import BaseModel, Field

from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_document_summary import KnowledgeDocumentSummary


class KnowledgeDocumentSelectionResult(BaseModel):
    """The documents a selection resolved to, cut at the caller's limit."""

    documents: Annotated[
        list[KnowledgeDocumentSummary], Field(description="Selected documents, sorted by collection and path.")
    ]
    truncated: Annotated[bool, Field(description="Whether more documents matched than the limit allowed.")] = False
