from typing import Annotated

from pydantic import BaseModel, Field

from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_document_summary import KnowledgeDocumentSummary
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_semantic_passage import KnowledgeSemanticPassage


class KnowledgeSemanticMatch(BaseModel):
    """A document a semantic search ranked, with the passages that ranked it."""

    summary: Annotated[KnowledgeDocumentSummary, Field(description="The document's listing entry")]
    score: Annotated[float, Field(description="The best passage's similarity, which ranks the document")]
    passages: Annotated[list[KnowledgeSemanticPassage], Field(description="Its closest passages, best first")]
