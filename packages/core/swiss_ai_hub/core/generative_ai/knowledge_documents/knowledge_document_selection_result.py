from typing import Annotated

from pydantic import BaseModel, Field

from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_document_summary import KnowledgeDocumentSummary
from swiss_ai_hub.core.generative_ai.knowledge_documents.path_date_counts import PathDateCounts


class KnowledgeDocumentSelectionResult(BaseModel):
    """The documents a selection resolved to, cut at the caller's limit."""

    documents: Annotated[
        list[KnowledgeDocumentSummary], Field(description="Selected documents, sorted by collection and path.")
    ]
    truncated: Annotated[bool, Field(description="Whether more documents matched than the limit allowed.")] = False
    path_dates: Annotated[
        PathDateCounts | None,
        Field(description="How the selection's period sorted the documents by their paths; null without a period."),
    ] = None
