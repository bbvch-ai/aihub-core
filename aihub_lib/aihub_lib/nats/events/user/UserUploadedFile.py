from typing import Annotated

from pydantic import BaseModel, Field


class UserUploadedFile(BaseModel):
    filename: Annotated[str, Field(description="The name of the uploaded file, including the extension.")]
    file_data: Annotated[str, Field(description="Base64 encoded content of the uploaded file.")]
    file_type: Annotated[
        str, Field(description="The MIME type of the uploaded file.", examples=["image/png", "application/pdf"])
    ]
