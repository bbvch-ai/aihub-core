from typing import Annotated

from pydantic import BaseModel, Field


class FileUploadRequest(BaseModel):
    """
    Request payload for initiating file upload to knowledge base.

    This request is used to get presigned URLs for direct S3/MinIO upload
    of files that will be processed and indexed in the knowledge base.
    """

    filename: Annotated[str, Field(description="Original filename of the file")]
    content_type: Annotated[str, Field(description="MIME type of the file")]
    content_length: Annotated[int, Field(description="Size of the file in bytes", gt=0, le=10485760)]  # 10MB max
    namespace_name: Annotated[str, Field(description="Target namespace name")]
    database_name: Annotated[str, Field(description="Target database name")]
