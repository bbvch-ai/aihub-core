from typing import Annotated

from pydantic import BaseModel, Field


class SignedUrlDto(BaseModel):
    url: Annotated[str, Field(..., description="The signed URL of the file")]
