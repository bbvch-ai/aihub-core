from datetime import datetime
from typing import Annotated, Literal, Optional

from llama_index.core.schema import TextNode
from pydantic import Field, BaseModel

from aihub_lib.persistence.rag.vectors.node_metadata import NAMESPACE, CREATED_AT, INSERTED_AT, UPDATED_AT, TYPE, \
    NodeTypeValue, DOCUMENT_TITLE, LANGUAGE, VERSION, INDEX, SECTION_START_LINE, SECTION_END_LINE, H1, H2, H5, H6, H4, \
    H3, HeadingLevelValue, HEADING_LEVEL, LanguageValue, NODE_TYPE_CONTENT


class NodeDTO(BaseModel):
    id: Annotated[str, Field(description="The unique identifier of the Node.")]
    text: Annotated[str, Field(description="The textual content of the Node.")]
    start_char_idx: Annotated[Optional[int], Field(description="The start character index of the Node.")]
    end_char_idx: Annotated[Optional[int], Field(description="The end character index of the Node.")]

    number_of_pages: Annotated[Optional[int], Field(description="Number of Pages in the Document.")]
    namespace: Annotated[str, Field(description="The namespace of the document within its metadata.")]
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
    inserted_at: Annotated[str, Field(description="Date source document was inserted into document store (ISO format string)")]


    @classmethod
    def from_llama_index_node(cls, node: TextNode):
        to_iso = lambda timestamp: datetime.fromtimestamp(timestamp).isoformat().replace("+00:00", "Z")
        return cls(
            id=node.node_id,
            text=node.text,
            start_char_idx=node.start_char_idx,
            end_char_idx=node.end_char_idx,

            number_of_pages=node.metadata.get("number_of_pages", 0),
            namespace=node.metadata.get(NAMESPACE),
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

            heading_level=node.metadata.get(HEADING_LEVEL,),

            created_at=to_iso(node.metadata.get(CREATED_AT, 0)),
            updated_at=to_iso(node.metadata.get(UPDATED_AT, 0)),
            inserted_at=to_iso(node.metadata.get(INSERTED_AT, 0)),

        )