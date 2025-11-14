from typing import Annotated

from pydantic import BaseModel, Field


class DocumentConversionMetadata(BaseModel):
    filename: Annotated[str, Field(..., description="Original filename of the converted document")]


class DocumentConversionResponse(BaseModel):
    page_content: Annotated[str, Field(..., description="Markdown content extracted from the document")]
    metadata: Annotated[DocumentConversionMetadata, Field(..., description="Metadata about the converted document")]
