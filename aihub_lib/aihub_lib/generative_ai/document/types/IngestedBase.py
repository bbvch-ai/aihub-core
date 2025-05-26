from typing import Annotated, Optional

from pydantic import BaseModel, Field

from aihub_lib.persistence.rag.vectors.node_metadata import LanguageValue


class IngestedBase(BaseModel):
    """
    Everything that is ingested, both nodes and documents, must have at least this set of metadata to ensure we know
    where the document was stored, what version the document is, etc.
    These attributes will hence be used to visualize retrieved documents etc. in the client UI.
    Note that all attributes that are specific to text documents, like number_of_pages, title, language, etc.,
    must be strictly optional, but all attributes that are purely technical like source are strictly necessary.
    """

    source: Annotated[str, Field(description="Source URI of original document.")]
    namespace: Annotated[str, Field(description="The namespace of the document within its metadata.")]
    version: Annotated[int, Field(description="Document version.")] = 1
    content_hash: Optional[str] = Field(
        None, description="Hash of the document/node, helpful to track whether file changed."
    )

    number_of_pages: Annotated[Optional[int], Field(description="Number of Pages in the Document.")] = None
    document_title: Annotated[Optional[str], Field(description="Document title.")] = None
    language: Annotated[Optional[LanguageValue], Field(description="Document language.")] = None

    created_at: Annotated[str, Field(description="Date source document was created (ISO format string)")]
    updated_at: Annotated[str, Field(description="Date source document was last updated (ISO format string)")]
    inserted_at: Annotated[
        str, Field(description="Date source document was inserted into document store (ISO format string)")
    ]
