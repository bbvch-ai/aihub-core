from typing import Annotated

from pydantic import BaseModel, Field


class DocumentUploadRequest(BaseModel):
    """
    Request payload for initiating document upload to knowledge base.

    This request is used to get presigned URLs for direct S3/MinIO upload
    of documents that will be processed and indexed in the knowledge base.
    """

    filename: Annotated[str, Field(description="Original filename of the document")]
    content_type: Annotated[str, Field(description="MIME type of the document")]
    content_length: Annotated[int, Field(description="Size of the document in bytes", gt=0, le=10485760)]  # 10MB max
    namespace: Annotated[str, Field(description="Target namespace/folder for the document")]
    database: Annotated[str, Field(description="Target database for the document")]
