from typing import Annotated

from pydantic import BaseModel, Field


class AgentFileUploadResponse(BaseModel):
    """Response containing a presigned upload URL and the assigned file_id."""

    upload_url: Annotated[str, Field(description="Presigned PUT URL for uploading the file.")]
    file_id: Annotated[str, Field(description="UUID4 file identifier — use this in subsequent API calls.")]
    expires_in: Annotated[int, Field(description="Seconds until the presigned URL expires.")]
