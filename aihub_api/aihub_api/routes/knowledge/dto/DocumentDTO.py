from datetime import datetime
from typing import Optional, Annotated, Literal
from pydantic import BaseModel, Field

from aihub_lib.persistence.rag.documents.entities.RefDoc import RefDoc


class DocumentDTO(BaseModel):
    id: Annotated[str, Field(description="The unique identifier of the document.")]
    document_type: Annotated[Optional[str], Field(default=None, description="The main type of the document entity.")]
    text: Annotated[str, Field(description="The textual content of the document.")]
    namespace: Annotated[str, Field(description="The namespace of the document within its metadata.")]

    title: Annotated[str, Field(description="Docuemnt title.")]
    number_of_pages: Annotated[int, Field(description="Number of Pages in the Document.")]
    content_type: Annotated[Literal["content", "summary"], Field(description="Content type (content or summary).")]

    created_at: Annotated[str, Field(description="Date source document was created (ISO format string)")]
    updated_at: Annotated[str, Field(description="Date source document was last updated (ISO format string)")]
    inserted_at: Annotated[str, Field(description="Date source document was inserted into document store (ISO format string)")]

    @staticmethod
    def from_entity(entity: RefDoc) -> "DocumentDTO":
        to_iso = lambda timestamp: datetime.fromtimestamp(timestamp).isoformat().replace("+00:00", "Z")
        return DocumentDTO(
            id=str(entity.id),
            document_type=entity.data.metadata.type,
            text=entity.data.text,
            namespace=entity.data.metadata.namespace,

            title=entity.data.metadata.document_title,
            number_of_pages=entity.data.metadata.number_of_pages,
            content_type=entity.data.metadata.type,

            created_at=to_iso(entity.data.metadata.created_at),
            updated_at=to_iso(entity.data.metadata.updated_at),
            inserted_at=to_iso(entity.data.metadata.inserted_at),
        )