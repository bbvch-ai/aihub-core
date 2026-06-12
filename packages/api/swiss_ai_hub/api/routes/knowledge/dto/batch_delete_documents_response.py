from typing import Annotated, Literal

from pydantic import BaseModel, Field

DocumentDeletionStatus = Literal["deleted", "not_found", "failed"]


class DocumentDeletionResult(BaseModel):
    """Outcome of a single document deletion within a batch request."""

    document_id: Annotated[str, Field(description="ID of the document")]
    status: Annotated[DocumentDeletionStatus, Field(description="Deletion outcome for this document")]


class BatchDeleteDocumentsResponse(BaseModel):
    """Per-document results of a best-effort batch deletion."""

    results: Annotated[list[DocumentDeletionResult], Field(description="Deletion outcome per requested document")]
