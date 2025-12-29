from datetime import UTC, datetime
from typing import Annotated

from aihub_lib.generative_ai.document.types.IngestedDocument import IngestedDocument
from aihub_lib.persistence.rag.datalake.entities.DatalakeFileEntity import DatalakeFileEntity, DatalakeFileStatus
from aihub_lib.persistence.rag.documents.entities.RefDoc import RefDoc
from pydantic import BaseModel, Field

S3_PROTOCOL_PREFIX = "s3://"


class DocumentDTO(BaseModel):
    id: Annotated[str, Field(description="Unique identifier of the document.")]
    source: Annotated[str, Field(description="Source path without protocol prefix (e.g., 'bucket/path/file.pdf').")]
    namespace: Annotated[str, Field(description="The namespace of the document within its metadata.")]
    created_at: Annotated[str, Field(description="Date source document was created (ISO format string)")]
    updated_at: Annotated[str, Field(description="Date source document was last updated (ISO format string)")]
    inserted_at: Annotated[
        str | None, Field(description="Date source document was inserted into document store (ISO format string)")
    ]
    is_ingested: Annotated[bool, Field(description="Indicates if the document has been ingested.")]
    status: Annotated[DatalakeFileStatus, Field(description="Current processing status of the document.")]
    content: Annotated[str | None, Field(description="Content of the document.")] = None
    number_of_pages: Annotated[int | None, Field(description="Number of Pages in the Document.")] = None
    document_title: Annotated[str | None, Field(description="Document title.")] = None

    @classmethod
    def from_ingested_document(cls, ingested_document: IngestedDocument) -> "DocumentDTO":
        return cls(
            id=ingested_document.id,
            content=ingested_document.content,
            is_ingested=True,
            status=DatalakeFileStatus.INGESTED,
            source=ingested_document.source.removeprefix(S3_PROTOCOL_PREFIX),
            namespace=ingested_document.namespace,
            number_of_pages=ingested_document.number_of_pages,
            document_title=ingested_document.document_title,
            created_at=ingested_document.created_at,
            updated_at=ingested_document.updated_at,
            inserted_at=ingested_document.inserted_at,
        )

    @classmethod
    def from_ref_doc(cls, entity: RefDoc) -> "DocumentDTO":
        def to_iso(timestamp: int):
            dt_utc = datetime.fromtimestamp(timestamp, tz=UTC)
            return dt_utc.isoformat().replace("+00:00", "Z")

        return cls(
            id=str(entity.id),
            content=entity.data.text,
            source=entity.data.metadata.source.removeprefix(S3_PROTOCOL_PREFIX),
            namespace=entity.data.metadata.namespace,
            number_of_pages=entity.data.metadata.number_of_pages,
            document_title=entity.data.metadata.document_title,
            created_at=to_iso(entity.data.metadata.created_at),
            updated_at=to_iso(entity.data.metadata.updated_at),
            inserted_at=to_iso(entity.data.metadata.inserted_at),
            is_ingested=True,
            status=DatalakeFileStatus.INGESTED,
        )

    @classmethod
    def from_datalake_file(cls, entity: DatalakeFileEntity, bucket_name: str) -> "DocumentDTO":
        """Create DTO from a datalake file entity (for processing files)."""

        def to_iso(timestamp: int) -> str:
            dt_utc = datetime.fromtimestamp(timestamp, tz=UTC)
            return dt_utc.isoformat().replace("+00:00", "Z")

        return cls(
            id=str(entity.id),
            source=f"{bucket_name}/{entity.file_path}",
            namespace=entity.namespace_name,
            document_title=entity.filename,
            created_at=to_iso(entity.created_at),
            updated_at=to_iso(entity.updated_at),
            inserted_at=None,
            is_ingested=entity.status == DatalakeFileStatus.INGESTED,
            status=entity.status,
        )
