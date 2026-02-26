from typing import Annotated

from pydantic import BaseModel, Field


class AgentFileUploadRequest(BaseModel):
    """Request to initiate a file upload to an agent's dedicated bucket."""

    filename: Annotated[
        str,
        Field(
            min_length=1,
            max_length=255,
            pattern=r"^[^/\\]+$",
            description="Original filename with extension. Must not contain path separators.",
        ),
    ]
    content_type: Annotated[
        str,
        Field(
            min_length=1,
            max_length=255,
            pattern=r"^[a-zA-Z0-9][a-zA-Z0-9!#$&\-^_]+/[a-zA-Z0-9][a-zA-Z0-9!#$&\-^_.+]*$",
            description="MIME type of the file (e.g. application/pdf, image/png).",
        ),
    ]
