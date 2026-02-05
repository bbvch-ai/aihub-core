from typing import Annotated, Any

from pydantic import BaseModel, Field


class DocumentConversionMetadata(BaseModel):
    """Metadata about the converted document."""

    source: Annotated[str, Field(description="Source filename")]
    filename: Annotated[str | None, Field(default=None, description="Original filename")]
    page: Annotated[int | None, Field(default=None, description="Page number if applicable")]
    # Allow additional custom fields
    model_config = {"extra": "allow"}


class DocumentConversionResponse(BaseModel):
    """
    Response schema for document conversion.

    Follows the OpenWebUI External Document Loader specification.
    Can return either a single document or a list of documents (one per page).
    """

    page_content: Annotated[str, Field(description="Extracted text content (markdown)")]
    metadata: Annotated[
        DocumentConversionMetadata | dict[str, Any] | None,
        Field(default=None, description="Document metadata"),
    ]
