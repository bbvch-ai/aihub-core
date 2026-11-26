from typing import Annotated, Self

from pydantic import BaseModel, Field, computed_field

from swiss_ai_hub.core.generative_ai.document.classification.normalized_date import NormalizedDate
from swiss_ai_hub.core.generative_ai.knowledge_documents.document_metadata_counts import DocumentMetadataCounts
from swiss_ai_hub.core.generative_ai.knowledge_documents.document_metadata_filter import DocumentMetadataFilter
from swiss_ai_hub.core.generative_ai.knowledge_documents.document_metadata_verdict import DocumentMetadataVerdict
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_document_summary import KnowledgeDocumentSummary
from swiss_ai_hub.core.generative_ai.knowledge_documents.path_date_counts import PathDateCounts
from swiss_ai_hub.core.generative_ai.knowledge_documents.path_date_parser import PathDateParser
from swiss_ai_hub.core.generative_ai.knowledge_documents.path_date_range import PathDateRange
from swiss_ai_hub.core.generative_ai.knowledge_documents.path_date_verdict import PathDateVerdict
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

    def dated_within(self, date_range: PathDateRange) -> tuple[Self, PathDateCounts]:
        """The documents a period keeps (every one its path does not date outside it), in order, with the counts.

        CPU-bound, one parse per path: callers in async code run it with `asyncio.to_thread`.
        """
        kept: list[KnowledgeDocumentSummary] = []
        outcomes: list[tuple[str, NormalizedDate | None, PathDateVerdict]] = []
        for document in self.documents:
            dated = PathDateParser.parse(document.path)
            verdict = date_range.verdict_of(dated)
            outcomes.append((document.path, dated, verdict))
            if verdict is not PathDateVerdict.OUTSIDE:
                kept.append(document)
        return self.model_copy(update={"documents": kept}), PathDateCounts.collect(outcomes, date_range)

    def with_metadata(
        self,
        metadata_filter: DocumentMetadataFilter,
        period: Annotated[
            PathDateRange | None, "The request's period, matched against each document's own date"
        ] = None,
    ) -> tuple[Self, DocumentMetadataCounts]:
        """The documents a metadata filter keeps (every one it does not exclude), in order, with the counts."""
        outcomes = [(document, metadata_filter.verdict(document, period)) for document in self.documents]
        kept = [document for document, verdict in outcomes if verdict is not DocumentMetadataVerdict.EXCLUDED]
        counts = DocumentMetadataCounts.collect([(document.path, verdict) for document, verdict in outcomes])
        return self.model_copy(update={"documents": kept}), counts
