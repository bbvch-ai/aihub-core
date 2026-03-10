from datetime import UTC, datetime
from typing import Annotated, Self

from llama_index.core import Document
from pydantic import Field

from swiss_ai_hub.core.generative_ai.document.types.IngestedBase import IngestedBase
from swiss_ai_hub.core.generative_ai.document.types.IngestedNode import IngestedNode
from swiss_ai_hub.core.persistence.rag.documents.entities.RefDoc import RefDoc
from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import (
    CREATED_AT,
    DOCUMENT_TITLE,
    INSERTED_AT,
    LANGUAGE,
    NAMESPACE,
    SOURCE,
    SOURCE_ORIGIN,
    UPDATED_AT,
    VERSION,
)


class IngestedDocument(IngestedBase):
    """
    Set of default metadata for a document or - what llama index calls it - a ref_doc. A ref doc is the databae
    representation of a document that was ingested through a pipeline. Hence, compared to the default data,
    we also have an ID and content that was parsed from the original file.
    """

    id: Annotated[str, Field(description="Unique identifier for the document.")]
    content: Annotated[str | None, Field(description="Content of the document.")] = None

    @classmethod
    def from_ref_doc(
        cls,
        ref_doc: Document,
    ) -> Self:
        def to_iso(timestamp: int):
            dt_utc = datetime.fromtimestamp(timestamp, tz=UTC)
            return dt_utc.isoformat().replace("+00:00", "Z")

        return cls(
            id=ref_doc.doc_id,
            content=ref_doc.text,
            source=ref_doc.metadata.get(SOURCE),
            source_origin=ref_doc.metadata.get(SOURCE_ORIGIN),
            namespace=ref_doc.metadata.get(NAMESPACE),
            document_title=ref_doc.metadata.get(DOCUMENT_TITLE, ""),
            language=ref_doc.metadata.get(LANGUAGE),
            version=ref_doc.metadata.get(VERSION, 1),
            created_at=to_iso(ref_doc.metadata.get(CREATED_AT, 0)),
            updated_at=to_iso(ref_doc.metadata.get(UPDATED_AT, 0)),
            inserted_at=to_iso(ref_doc.metadata.get(INSERTED_AT, 0)),
        )

    @classmethod
    def from_node(
        cls,
        node: IngestedNode,
        document_id: str | None = None,
        content: str | None = None,
    ) -> Self:
        return cls(
            id=document_id or node.document_id,
            content=content or node.content,
            source=node.source,
            source_origin=node.source_origin,
            namespace=node.namespace,
            number_of_pages=node.number_of_pages,
            document_title=node.document_title,
            language=node.language,
            version=node.version,
            created_at=node.created_at,
            updated_at=node.updated_at,
            inserted_at=node.inserted_at,
        )

    @classmethod
    def from_entity(cls, entity: RefDoc) -> Self:
        def to_iso(timestamp: int):
            dt_utc = datetime.fromtimestamp(timestamp, tz=UTC)
            return dt_utc.isoformat().replace("+00:00", "Z")

        return cls(
            id=str(entity.id),
            content=entity.data.text,
            source=entity.data.metadata.source,
            source_origin=entity.data.metadata.source_origin,
            namespace=entity.data.metadata.namespace,
            number_of_pages=entity.data.metadata.number_of_pages,
            document_title=entity.data.metadata.document_title,
            language=entity.data.metadata.language,
            version=entity.data.metadata.version or 1,
            created_at=to_iso(entity.data.metadata.created_at),
            updated_at=to_iso(entity.data.metadata.updated_at),
            inserted_at=to_iso(entity.data.metadata.inserted_at),
        )
