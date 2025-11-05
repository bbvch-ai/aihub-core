from typing import Annotated

from pydantic import BaseModel, Field


class DocumentUploadValidationResponse(BaseModel):
    """
    Response containing the validation result of a file upload.

    This response indicates whether the uploaded file exists in the globally
    configured datalake and provides information about the validation process.
    """

    exists: Annotated[bool, Field(description="Whether the file exists in the datalake")]
    file_path: Annotated[str, Field(description="Path/key of the file that was validated")]
    container: Annotated[str, Field(description="Name of the container/bucket")]
