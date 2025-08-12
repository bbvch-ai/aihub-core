from typing import Annotated

from pydantic import BaseModel, Field


class DocumentUploadCompleteRequest(BaseModel):
    """
    Request payload for completing document upload after successful S3/MinIO upload.

    This request notifies the system that the document has been successfully
    uploaded to S3/MinIO and should be processed for indexing in the knowledge base.
    """

    upload_id: Annotated[str, Field(description="Unique identifier for the upload session")]
    container: Annotated[str, Field(description="S3 bucket/container name where document was stored")]
    object_key: Annotated[str, Field(description="S3 object key/path of the uploaded document")]
    namespace: Annotated[str, Field(description="Target namespace for the document")]
    database: Annotated[str, Field(description="Target database for the document")]
