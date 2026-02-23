import asyncio
from typing import Annotated

import boto3
from botocore.config import Config
from pydantic import BaseModel, Field

from aihub_lib.infrastructure.s3.S3StorageSettings import S3StorageSettings


class UserUploadedFile(BaseModel):
    filename: Annotated[str, Field(description="The name of the uploaded file, including the extension.")]
    file_type: Annotated[
        str, Field(description="The MIME type of the uploaded file.", examples=["image/png", "application/pdf"])
    ]
    s3_bucket: Annotated[str, Field(description="The S3 bucket where the file is stored.")]
    s3_key: Annotated[str, Field(description="The S3 object key for the file.")]

    async def fetch_content(self) -> bytes:
        """Download the file content from S3 on demand."""
        settings = S3StorageSettings()
        client = boto3.client(
            "s3",
            endpoint_url=settings.ENDPOINT,
            aws_access_key_id=settings.ACCESS_KEY,
            aws_secret_access_key=settings.SECRET_KEY.get_secret_value(),
            region_name=settings.REGION,
            config=Config(signature_version="s3v4"),
        )

        def _download() -> bytes:
            response = client.get_object(Bucket=self.s3_bucket, Key=self.s3_key)
            return response["Body"].read()

        return await asyncio.to_thread(_download)