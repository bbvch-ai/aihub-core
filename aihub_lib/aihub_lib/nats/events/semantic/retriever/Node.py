from datetime import datetime
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
    start_char_idx: Annotated[Optional[int], Field(description="The start character index of the Node.")]
    end_char_idx: Annotated[Optional[int], Field(description="The end character index of the Node.")]

    document_id: Annotated[str, Field(description="ID of original ref_doc.")]
    source_uri: Annotated[str, Field(description="Source URI of original document.")]
    namespace: Annotated[str, Field(description="The namespace of the document within its metadata.")]

    number_of_pages: Annotated[Optional[int], Field(description="Number of Pages in the Document.")]
    content_type: Annotated[NodeTypeValue, Field(description="Content type (content or summary).")]
    title: Annotated[str, Field(description="Document title.")]
    language: Annotated[LanguageValue, Field(description="Node language.")]
    version: Annotated[int, Field(description="Node version.")]
    index: Annotated[int, Field(description="Index counting position of node in document")]

    section_start_line: Annotated[int, Field(description="Start line of the node in document")]
    section_end_line: Annotated[int, Field(description="End line of the node in document")]

    h1: Annotated[Optional[str], Field(description="H1 of the node in document")]
    h2: Annotated[Optional[str], Field(description="H2 of the node in document")]
    h3: Annotated[Optional[str], Field(description="H3 of the node in document")]
    h4: Annotated[Optional[str], Field(description="H4 of the node in document")]
    h5: Annotated[Optional[str], Field(description="H5 of the node in document")]
    h6: Annotated[Optional[str], Field(description="H6 of the node in document")]

    heading_level: Annotated[HeadingLevelValue, Field(description="Heading level of the node in document")]

    created_at: Annotated[str, Field(description="Date source document was created (ISO format string)")]
    updated_at: Annotated[str, Field(description="Date source document was last updated (ISO format string)")]
    inserted_at: Annotated[
        str, Field(description="Date source document was inserted into document store (ISO format string)")
    ]

    score: Annotated[Optional[float], Field(description="Score representing the relevance of the document.")] = None

    @classmethod
    def from_llama_index_node(cls, node: TextNode):
        def to_iso(timestamp: int):
            return datetime.fromtimestamp(timestamp).isoformat().replace("+00:00", "Z")

        return cls(
            id=node.node_id,
            text=node.text,
            start_char_idx=node.start_char_idx,
            end_char_idx=node.end_char_idx,
            document_id=node.ref_doc_id
            or node.metadata.get(DOCUMENT_ID, node.metadata.get("doc_id", node.metadata.get("ref_doc_id"))),
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
