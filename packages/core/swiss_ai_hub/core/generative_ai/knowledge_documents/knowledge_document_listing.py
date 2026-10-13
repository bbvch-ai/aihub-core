from typing import Annotated, Self

from pydantic import BaseModel, Field, computed_field

from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_document_summary import KnowledgeDocumentSummary
from swiss_ai_hub.core.generative_ai.knowledge_documents.path_glob import PathGlob
from swiss_ai_hub.core.generative_ai.knowledge_documents.path_regex import PathRegex


class KnowledgeDocumentListing(BaseModel):
    """The ingested documents of some collections, narrowed by chained path filters.

    Each filter returns a new listing, so a caller can fix a glob first and let further patterns only narrow it.
    Documents stay sorted by database, collection and path, so a caller that shows the listing page by page sees every
    document exactly once.
    """

    documents: Annotated[list[KnowledgeDocumentSummary], Field(description="Documents, sorted by collection and path")]

    @classmethod
    def from_summaries(cls, summaries: list[KnowledgeDocumentSummary]) -> Self:
        return cls(
            documents=sorted(
                summaries,
                key=lambda summary: (summary.collection.bucket_name, summary.collection.namespace_name, summary.path),
            )
        )

    @computed_field
    @property
    def total(self) -> int:
        return len(self.documents)

    def matching_glob(self, pattern: str) -> Self:
        glob = PathGlob(pattern)
        return self.model_copy(update={"documents": [doc for doc in self.documents if glob.matches(doc.path)]})

    def matching_regex(self, pattern: str) -> Self:
        matched = PathRegex(pattern).matches_all([doc.path for doc in self.documents])
        return self.model_copy(
            update={"documents": [doc for doc, is_match in zip(self.documents, matched, strict=True) if is_match]}
        )
