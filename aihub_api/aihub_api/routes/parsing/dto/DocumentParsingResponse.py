from typing import Annotated

from pydantic import BaseModel, Field


class DocumentParsingMetadata(BaseModel):
    """Metadata about the converted document."""

    filename: Annotated[str, Field(description="Original filename")]


class DocumentParsingResponse(BaseModel):
    """
    Response schema for document conversion.

    Follows the OpenWebUI External Document Loader specification.
    Can return either a single document or a list of documents (one per page).
    """

    page_content: Annotated[str, Field(description="Extracted text content (markdown)")]
    metadata: Annotated[
        DocumentParsingMetadata | None,
        Field(default=None, description="Document metadata"),
    ]
