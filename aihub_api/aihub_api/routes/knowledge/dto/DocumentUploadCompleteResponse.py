from typing import Annotated

from pydantic import BaseModel, Field


class DocumentUploadCompleteResponse(BaseModel):
    """
    Response payload for completed document upload.

    Confirms that the document has been successfully received and
    queued for processing in the knowledge base pipeline.
    """

    success: Annotated[bool, Field(description="Whether the upload completion was successful")]
    document_id: Annotated[str, Field(description="Unique identifier assigned to the uploaded document")]
    message: Annotated[str, Field(description="Human-readable status message")]
    processing_status: Annotated[
        str, Field(description="Current processing status (queued, processing, completed, error)")
    ]
