from datetime import datetime, timezone
from typing import Annotated, Optional

from llama_index.core.schema import NodeWithScore, TextNode
from pydantic import BaseModel, Field

from aihub_lib.persistence.rag.vectors.node_metadata import (
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
    NODE_TYPE_CONTENT,
    SECTION_END_LINE,
    SECTION_START_LINE,
    SOURCE,
    TYPE,
    UPDATED_AT,
    VERSION,
    HeadingLevelValue,
    LanguageValue,
    NodeTypeValue,
)


class Node(BaseModel):
    id: Annotated[str, Field(description="The unique identifier of the Node.")]
    text: Annotated[str, Field(description="The textual content of the Node.")]
    content_type: Annotated[NodeTypeValue, Field(description="Content type (content or summary).")] = "content"

    start_char_idx: Annotated[Optional[int], Field(description="The start character index of the Node.")] = None
    end_char_idx: Annotated[Optional[int], Field(description="The end character index of the Node.")] = None

    document_id: Annotated[str, Field(description="ID of original ref_doc.")]
    source_uri: Annotated[str, Field(description="Source URI of original document.")]
    namespace: Annotated[str, Field(description="The namespace of the document within its metadata.")]

    number_of_pages: Annotated[Optional[int], Field(description="Number of Pages in the Document.")] = None
    title: Annotated[Optional[str], Field(description="Document title.")] = None
    language: Annotated[Optional[LanguageValue], Field(description="Node language.")] = None
    version: Annotated[int, Field(description="Node version.")] = 1

    index: Annotated[Optional[int], Field(description="Index counting position of node in document")] = None
    section_start_line: Annotated[Optional[int], Field(description="Start line of the node in document")] = None
    section_end_line: Annotated[Optional[int], Field(description="End line of the node in document")] = None

    h1: Annotated[Optional[str], Field(description="H1 of the node in document")] = None
    h2: Annotated[Optional[str], Field(description="H2 of the node in document")] = None
    h3: Annotated[Optional[str], Field(description="H3 of the node in document")] = None
    h4: Annotated[Optional[str], Field(description="H4 of the node in document")] = None
    h5: Annotated[Optional[str], Field(description="H5 of the node in document")] = None
    h6: Annotated[Optional[str], Field(description="H6 of the node in document")] = None

    heading_level: Annotated[
        Optional[HeadingLevelValue], Field(description="Heading level of the node in document")
    ] = None

    created_at: Annotated[str, Field(description="Date source document was created (ISO format string)")]
    updated_at: Annotated[str, Field(description="Date source document was last updated (ISO format string)")]
    inserted_at: Annotated[
        str, Field(description="Date source document was inserted into document store (ISO format string)")
    ]

    score: Annotated[Optional[float], Field(description="Score representing the relevance of the document.")] = None

    @classmethod
    def from_llama_index_node(cls, node: TextNode):
        def to_iso(timestamp: int):
            dt_utc = datetime.fromtimestamp(timestamp, tz=timezone.utc)
            return dt_utc.isoformat().replace("+00:00", "Z")

        document_id = node.ref_doc_id or node.metadata.get(
            DOCUMENT_ID, node.metadata.get("doc_id", node.metadata.get("ref_doc_id"))
        )
        return cls(
            id=node.node_id,
            text=node.text,
            start_char_idx=getattr(node, "start_char_idx", None),
            end_char_idx=getattr(node, "end_char_idx", None),
            document_id=document_id,
            source_uri=node.metadata.get(SOURCE),
            namespace=node.metadata.get(NAMESPACE),
            number_of_pages=node.metadata.get("number_of_pages", 0),
            content_type=node.metadata.get(TYPE, NODE_TYPE_CONTENT),
            title=node.metadata.get(DOCUMENT_TITLE, ""),
            language=node.metadata.get(LANGUAGE),
            version=node.metadata.get(VERSION, 1),
            index=node.metadata.get(INDEX, 0),
            section_start_line=node.metadata.get(SECTION_START_LINE),
            section_end_line=node.metadata.get(SECTION_END_LINE),
            h1=node.metadata.get(H1),
            h2=node.metadata.get(H2),
            h3=node.metadata.get(H3),
            h4=node.metadata.get(H4),
            h5=node.metadata.get(H5),
            h6=node.metadata.get(H6),
            heading_level=node.metadata.get(
                HEADING_LEVEL,
            ),
            created_at=to_iso(node.metadata.get(CREATED_AT, 0)),
            updated_at=to_iso(node.metadata.get(UPDATED_AT, 0)),
            inserted_at=to_iso(node.metadata.get(INSERTED_AT, 0)),
        )

    @classmethod
    def from_llama_index_node_with_score(cls, node_with_score: NodeWithScore):
        node = cls.from_llama_index_node(node_with_score.node)
        node.score = node_with_score.score
        return node
