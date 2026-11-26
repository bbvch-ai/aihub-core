from datetime import UTC, datetime
from pathlib import PurePosixPath
from typing import Annotated, Self

from pydantic import BaseModel, Field

from swiss_ai_hub.core.generative_ai.document.classification.document_type_catalog import DocumentTypeCatalog
from swiss_ai_hub.core.generative_ai.knowledge_documents.resolved_knowledge_collection import (
    ResolvedKnowledgeCollection,
)
from swiss_ai_hub.core.generative_ai.retrievers.bucket_namespace_pair import BucketNamespacePair
from swiss_ai_hub.core.persistence.rag.documents.entities.ref_doc import Metadata, RefDoc


class KnowledgeDocumentSummary(BaseModel):
    """One ingested document as a listing shows it: everything needed to pick it, nothing of its text."""

    id: Annotated[str, Field(description="Document id, unique within its knowledge database")]
    collection: Annotated[BucketNamespacePair, Field(description="Collection the document belongs to")]
    path: Annotated[str, Field(description="Path relative to the collection, e.g. 'invoices/2025/acme.pdf'")]
    filename: Annotated[str, Field(description="Last segment of the path")]
    title: Annotated[str, Field(description="Document title, the filename when the document has none")]
    file_type: Annotated[str, Field(description="Lower-case file extension without the dot, e.g. 'pdf'")]
    number_of_pages: Annotated[int | None, Field(description="Page count when the parser reported one")] = None
    updated_at: Annotated[datetime, Field(description="When the source file last changed")]
    document_type: Annotated[
        str | None, Field(description="Type from ingestion's classification; None when the document was not classified")
    ] = None
    document_types: Annotated[list[str], Field(description="Every type of the document, primary first")] = []
    document_attributes: Annotated[
        dict[str, str | float | list[str] | None],
        Field(description="Classified attribute values under their metadata keys; None where unknown"),
    ] = {}

    @classmethod
    def from_ref_doc(cls, ref_doc: RefDoc, resolved: ResolvedKnowledgeCollection) -> Self:
        metadata = ref_doc.data.metadata
        path = resolved.relative_path(metadata.source)
        filename = PurePosixPath(path).name
        return cls(
            id=str(ref_doc.id),
            collection=resolved.collection,
            path=path,
            filename=filename,
            title=metadata.document_title or filename,
            file_type=cls._file_type(filename, ref_doc.data.mimetype),
            number_of_pages=metadata.number_of_pages,
            updated_at=datetime.fromtimestamp(metadata.updated_at, tz=UTC),
            document_type=metadata.document_type,
            document_types=list(metadata.document_types or []),
            document_attributes=cls._attributes(metadata) if metadata.document_type else {},
        )

    @staticmethod
    def _attributes(metadata: Metadata) -> dict[str, str | float | list[str] | None]:
        """The stored values, without the copied text they were read from: a listing selects, it does not audit."""
        return {key: getattr(metadata, key, None) for key in DocumentTypeCatalog.value_keys()}

    @staticmethod
    def _file_type(filename: str, mimetype: str | None) -> str:
        """`metadata.type` is always "content", so the extension is the only reliable signal of the file's type."""
        extension = PurePosixPath(filename).suffix.lower().removeprefix(".")
        return extension or mimetype or "unknown"
