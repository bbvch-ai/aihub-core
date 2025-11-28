from typing import Annotated

from pydantic import BaseModel, Field


class UpdateMemoryRequest(BaseModel):
    """Request for updating a memory's content."""

    data: Annotated[str, Field(description="New content to update the memory with.")]
