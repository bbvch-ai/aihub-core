from typing import Annotated

from pydantic import BaseModel, Field


class UserUploadedFile(BaseModel):
    filename: Annotated[str, Field(description="The name of the uploaded file, including the extension.")]
    file_type: Annotated[
        str, Field(description="The MIME type of the uploaded file.", examples=["image/png", "application/pdf"])
    ]
    s3_bucket: Annotated[str, Field(description="The S3 bucket where the file is stored.")]
    s3_key: Annotated[str, Field(description="The S3 object key for the file.")]
