from datetime import datetime, timezone
from typing import Annotated, Optional

from llama_index.core import Document
from pydantic import Field

from aihub_lib.generative_ai.document.types.IngestedBase import IngestedBase
from aihub_lib.generative_ai.document.types.IngestedNode import IngestedNode
from aihub_lib.persistence.rag.documents.entities.RefDoc import RefDoc
from aihub_lib.persistence.rag.vectors.node_metadata import (
    CREATED_AT,
    DOCUMENT_TITLE,
    INSERTED_AT,
    LANGUAGE,
    NAMESPACE,
    SOURCE,
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
    content: Annotated[str, Field(description="Content of the document.")] = None

    @classmethod
    def from_ref_doc(
        cls,
        ref_doc: Document,
    ) -> "IngestedDocument":
        def to_iso(timestamp: int):
            dt_utc = datetime.fromtimestamp(timestamp, tz=timezone.utc)
            return dt_utc.isoformat().replace("+00:00", "Z")

        return cls(
            id=ref_doc.doc_id,
            content=ref_doc.text,
            source=ref_doc.metadata.get(SOURCE),
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
        document_id: Optional[str] = None,
        content: Optional[str] = None,
    ) -> "IngestedDocument":
        return cls(
            id=document_id or node.document_id,
            content=content or node.content,
            source=node.source,
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
    def from_entity(cls, entity: RefDoc) -> "IngestedDocument":
        def to_iso(timestamp: int):
            dt_utc = datetime.fromtimestamp(timestamp, tz=timezone.utc)
            return dt_utc.isoformat().replace("+00:00", "Z")

        return cls(
            id=str(entity.id),
            content=entity.data.text,
            source=entity.data.metadata.source,
            namespace=entity.data.metadata.namespace,
            number_of_pages=entity.data.metadata.number_of_pages,
            document_title=entity.data.metadata.document_title,
            language=entity.data.metadata.language,
            version=entity.data.metadata.version or 1,
            created_at=to_iso(entity.data.metadata.created_at),
            updated_at=to_iso(entity.data.metadata.updated_at),
            inserted_at=to_iso(entity.data.metadata.inserted_at),
        )
