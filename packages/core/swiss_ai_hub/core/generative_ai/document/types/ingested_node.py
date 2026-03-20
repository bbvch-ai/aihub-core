import json
from datetime import UTC, datetime
from typing import Annotated

from llama_index.core.schema import BaseNode, NodeWithScore, TextNode
from openinference.semconv.trace import DocumentAttributes
from pydantic import Field

from swiss_ai_hub.core.generative_ai.document.types.ingested_base import IngestedBase
from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import (
    CREATED_AT,
    DOCUMENT_ID,
    DOCUMENT_TITLE,
    H1,
    H2,
    H3,
    H4,
    H5,
    H6,
    HEADING_LEVEL,
    INDEX,
    INSERTED_AT,
    LANGUAGE,
    NAMESPACE,
    NODE_CONTENT,
    NODE_CONTENT_TYPE,
    NODE_CONTENT_TYPE_TEXT,
    NODE_LANGUAGE_GERMAN,
    NODE_TYPE_CONTENT,
    NUMBER_OF_PAGES,
    SECTION_END_LINE,
    SECTION_START_LINE,
    SOURCE,
    SOURCE_ORIGIN,
    TYPE,
    UPDATED_AT,
    VERSION,
    HeadingLevelValue,
    NodeContentType,
    NodeTypeValue,
)


class IngestedNode(IngestedBase):
    """
    A node represents a chunk of a document, like a paragraph, produced by a document parser and text splitter.
    The attributes defined here are the minimal number of attributes that a node must have to ensure the
    UI can properly display it. Note that all attributes that are specific to text documents, like start_char_idx etc.
    must be strictly optional, as we don't really know whether the node is indeed a text node. However, all attributes
    that are purely technical, like the document_id to keep the back-ref to the ref_doc from which the node originates,
    are strictly necessary.
    """

    id: Annotated[str, Field(description="The unique identifier of the Node.")]
    content: Annotated[str, Field(description="The textual content of the Node.")]
    type: Annotated[NodeTypeValue, Field(description="Type (content or summary).")] = NODE_CONTENT
    content_type: Annotated[NodeContentType, Field(description="Content type (text, figure or table).")] = (
        NODE_CONTENT_TYPE_TEXT
    )
    document_id: Annotated[str, Field(description="ID of original ref_doc.")]

    start_char_idx: Annotated[int | None, Field(description="The start character index of the Node.")] = None
    end_char_idx: Annotated[int | None, Field(description="The end character index of the Node.")] = None

    index: Annotated[int | None, Field(description="Index counting position of node in document")] = None
    section_start_line: Annotated[int | None, Field(description="Start line of the node in document")] = None
    section_end_line: Annotated[int | None, Field(description="End line of the node in document")] = None

    h1: Annotated[str | None, Field(description="H1 of the node in document")] = None
    h2: Annotated[str | None, Field(description="H2 of the node in document")] = None
    h3: Annotated[str | None, Field(description="H3 of the node in document")] = None
    h4: Annotated[str | None, Field(description="H4 of the node in document")] = None
    h5: Annotated[str | None, Field(description="H5 of the node in document")] = None
    h6: Annotated[str | None, Field(description="H6 of the node in document")] = None

    heading_level: Annotated[HeadingLevelValue | None, Field(description="Heading level of the node in document")] = (
        None
    )

    score: Annotated[float | None, Field(description="Score representing the relevance of the document.")] = None

    @classmethod
    def from_llama_index_node(cls, node: TextNode | BaseNode):
        def to_iso(timestamp: int):
            dt_utc = datetime.fromtimestamp(timestamp, tz=UTC)
            return dt_utc.isoformat().replace("+00:00", "Z")

        document_id = node.ref_doc_id or node.metadata.get(
            DOCUMENT_ID, node.metadata.get("doc_id", node.metadata.get("ref_doc_id"))
        )

        metadata = node.metadata.copy() if node.metadata else {}
        inst = cls(
            id=node.node_id,
            content=node.text,
            start_char_idx=getattr(node, "start_char_idx", None),
            end_char_idx=getattr(node, "end_char_idx", None),
            document_id=document_id,
            source=metadata.pop(SOURCE),
            source_origin=metadata.pop(SOURCE_ORIGIN, None),
            namespace=metadata.pop(NAMESPACE),
            type=metadata.pop(TYPE, NODE_TYPE_CONTENT),
            content_type=metadata.pop(NODE_CONTENT_TYPE, NODE_CONTENT_TYPE_TEXT),
            document_title=metadata.pop(DOCUMENT_TITLE, ""),
            language=metadata.pop(LANGUAGE, NODE_LANGUAGE_GERMAN),
            version=metadata.pop(VERSION, 1),
            index=metadata.pop(INDEX, 0),
            section_start_line=metadata.pop(SECTION_START_LINE, None),
            section_end_line=metadata.pop(SECTION_END_LINE, None),
            h1=metadata.pop(H1, None),
            h2=metadata.pop(H2, None),
            h3=metadata.pop(H3, None),
            h4=metadata.pop(H4, None),
            h5=metadata.pop(H5, None),
            h6=metadata.pop(H6, None),
            heading_level=metadata.pop(HEADING_LEVEL, None),
            created_at=to_iso(metadata.pop(CREATED_AT, 0)),
            updated_at=to_iso(metadata.pop(UPDATED_AT, 0)),
            inserted_at=to_iso(metadata.pop(INSERTED_AT, 0)),
            metadata=metadata,
        )

        return inst

    @classmethod
    def from_llama_index_node_with_score(cls, node_with_score: NodeWithScore):
        node = cls.from_llama_index_node(node_with_score.node)
        node.score = node_with_score.score
        return node

    def to_llama_index_node_with_score(self) -> NodeWithScore:
        def from_iso(iso_string: str) -> int:
            """Convert ISO timestamp string to Unix timestamp integer."""
            dt = datetime.fromisoformat(iso_string.replace("Z", "+00:00"))
            return int(dt.timestamp())

        node = TextNode(
            id_=self.id,
            text=self.content,
            metadata={
                TYPE: self.type,
                NODE_CONTENT_TYPE: self.content_type,
                DOCUMENT_ID: self.document_id,
                SOURCE: self.source,
                SOURCE_ORIGIN: self.source_origin,
                NAMESPACE: self.namespace,
                DOCUMENT_TITLE: self.document_title,
                LANGUAGE: self.language,
                VERSION: self.version,
                INDEX: self.index,
                SECTION_START_LINE: self.section_start_line,
                SECTION_END_LINE: self.section_end_line,
                H1: self.h1,
                H2: self.h2,
                H3: self.h3,
                H4: self.h4,
                H5: self.h5,
                H6: self.h6,
                HEADING_LEVEL: self.heading_level,
                CREATED_AT: from_iso(self.created_at),
                UPDATED_AT: from_iso(self.updated_at),
                INSERTED_AT: from_iso(self.inserted_at),
                **self.metadata,
            },
            ref_doc_id=self.document_id,
        )

        if self.start_char_idx is not None:
            node.start_char_idx = self.start_char_idx
        if self.end_char_idx is not None:
            node.end_char_idx = self.end_char_idx

        return NodeWithScore(node=node, score=self.score)

    def to_semantic_convention(self, key: str, i: int) -> dict[str, str]:
        return {
            f"{key}.{i}.{DocumentAttributes.DOCUMENT_ID}": self.id,
            f"{key}.{i}.{DocumentAttributes.DOCUMENT_SCORE}": self.score,
            f"{key}.{i}.{DocumentAttributes.DOCUMENT_CONTENT}": self.content,
            f"{key}.{i}.{DocumentAttributes.DOCUMENT_METADATA}": json.dumps(
                {
                    DOCUMENT_ID: self.document_id,
                    SOURCE: self.source,
                    SOURCE_ORIGIN: self.source_origin,
                    NAMESPACE: self.namespace,
                    NUMBER_OF_PAGES: self.number_of_pages,
                    DOCUMENT_TITLE: self.document_title,
                    LANGUAGE: self.language,
                    VERSION: self.version,
                    CREATED_AT: self.created_at,
                    UPDATED_AT: self.updated_at,
                    INSERTED_AT: self.inserted_at,
                }
            ),
        }
