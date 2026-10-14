from typing import Annotated, Self

from pydantic import BaseModel, Field

from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_document_summary import KnowledgeDocumentSummary
from swiss_ai_hub.core.generative_ai.retrievers.bucket_namespace_pair import BucketNamespacePair


class RecordProvenance(BaseModel):
    """The document a record was extracted from, so every row of a result can name its source."""

    document_id: Annotated[str, Field(description="Document id, unique within its knowledge database")]
    collection: Annotated[BucketNamespacePair, Field(description="Collection the document belongs to")]
    path: Annotated[str, Field(description="Path relative to the collection, e.g. 'invoices/2025/acme.pdf'")]
    filename: Annotated[str, Field(description="Last segment of the path")]
    title: Annotated[str, Field(description="Document title, the filename when the document has none")]
    page: Annotated[
        int | None,
        Field(description="Page the record was found on. None while parsed text carries no page boundaries"),
    ] = None

    @classmethod
    def from_summary(cls, summary: KnowledgeDocumentSummary) -> Self:
        return cls(
            document_id=summary.id,
            collection=summary.collection,
            path=summary.path,
            filename=summary.filename,
            title=summary.title,
        )
