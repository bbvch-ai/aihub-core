from typing import Annotated

from pydantic import BaseModel, Field

from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import LanguageValue


class IngestedBase(BaseModel):
    """
    Everything that is ingested, both nodes and documents, must have at least this set of metadata to ensure we know
    where the document was stored, what version the document is, etc.
    These attributes will hence be used to visualize retrieved documents etc. in the client UI.
    Note that all attributes that are specific to text documents, like number_of_pages, title, language, etc.,
    must be strictly optional, but all attributes that are purely technical like source are strictly necessary.
    """

    source: Annotated[str, Field(description="Source URI (data lake URI).")]
    source_origin: Annotated[
        str | None, Field(description="Original source URI (e.g., SharePoint URL, external URL).")
    ] = None
    namespace: Annotated[str, Field(description="The namespace of the document within its metadata.")]
    version: Annotated[int, Field(description="Document version.")] = 1
    content_hash: Annotated[
        str | None, Field(description="Hash of the document/node, helpful to track whether file changed.")
    ] = None

    number_of_pages: Annotated[int | None, Field(description="Number of Pages in the Document.")] = None
    document_title: Annotated[str | None, Field(description="Document title.")] = None
    language: Annotated[LanguageValue | None, Field(description="Document language.")] = None

    created_at: Annotated[str, Field(description="Date source document was created (ISO format string)")]
    updated_at: Annotated[str, Field(description="Date source document was last updated (ISO format string)")]
    inserted_at: Annotated[
        str, Field(description="Date source document was inserted into document store (ISO format string)")
    ]
    metadata: Annotated[dict | None, Field(description="Additional metadata for the document.")] = None
