from typing import Annotated

from pydantic import BaseModel, Field


class FileUploadValidationRequest(BaseModel):
    """
    Request for validating whether a file was successfully uploaded to cloud storage.

    This request contains the information needed to verify that a file upload completed
    successfully in the globally configured datalake (S3, MinIO, or Azure Blob Storage).
    """

    container: Annotated[str, Field(description="Name of the container/bucket where the file was uploaded")]
    file_path: Annotated[str, Field(description="Path/key of the uploaded file within the container")]
