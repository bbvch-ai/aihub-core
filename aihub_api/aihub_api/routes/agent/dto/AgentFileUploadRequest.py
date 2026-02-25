from typing import Annotated

from pydantic import BaseModel, Field


class AgentFileUploadRequest(BaseModel):
    """Request to initiate a file upload to an agent's dedicated bucket."""

    filename: Annotated[str, Field(min_length=1, max_length=255, description="Original filename with extension.")]
    content_type: Annotated[str, Field(min_length=1, description="MIME type of the file.")]
