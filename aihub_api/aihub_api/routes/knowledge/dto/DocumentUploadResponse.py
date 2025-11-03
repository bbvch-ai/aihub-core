from typing import Annotated

from pydantic import BaseModel, Field


class DocumentUploadResponse(BaseModel):
    """
    Response payload for file upload initialization.

    Contains the presigned URL for direct datalake upload and metadata
    needed to complete the upload process.
    """

    upload_url: Annotated[str, Field(description="Presigned URL for uploading the file to a datalake")]
    upload_id: Annotated[str, Field(description="Unique identifier for this upload session")]
    container: Annotated[str, Field(description="The bucket/container name where file will be stored")]
    folder: Annotated[str, Field(description="The folder name within the bucket/container")]
    object_key: Annotated[str, Field(description="The object key/path for the uploaded file")]
    expires_in: Annotated[int, Field(description="Upload URL expiration time in seconds")]
