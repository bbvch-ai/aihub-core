from typing import Annotated

from pydantic import BaseModel, Field


class DocumentUploadResponse(BaseModel):
    """
    Response payload for document upload initialization.

    Contains the presigned URL for direct S3/MinIO upload and metadata
    needed to complete the upload process.
    """

    upload_url: Annotated[str, Field(description="Presigned URL for uploading the document to S3/MinIO")]
    upload_id: Annotated[str, Field(description="Unique identifier for this upload session")]
    container: Annotated[str, Field(description="S3 bucket/container name where document will be stored")]
    object_key: Annotated[str, Field(description="S3 object key/path for the uploaded document")]
    expires_in: Annotated[int, Field(description="Upload URL expiration time in seconds")]

    # Fields to be sent back after successful upload
    namespace: Annotated[str, Field(description="Target namespace for the document")]
    database: Annotated[str, Field(description="Target database for the document")]
