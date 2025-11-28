from typing import Annotated

from pydantic import BaseModel, Field


class UpdateMemoryResponse(BaseModel):
    """Response for updating a memory."""

    status: Annotated[str, Field(description="Update status.")]
    memory_id: Annotated[str, Field(description="ID of the updated memory.")]
