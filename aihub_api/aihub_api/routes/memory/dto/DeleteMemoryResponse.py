from typing import Annotated

from pydantic import BaseModel, Field


class DeleteMemoryResponse(BaseModel):
    """Response for deleting a single memory."""

    status: Annotated[str, Field(description="Deletion status.")]
    memory_id: Annotated[str, Field(description="ID of the deleted memory.")]


class DeleteAllMemoriesResponse(BaseModel):
    """Response for deleting all memories."""

    status: Annotated[str, Field(description="Deletion status.")]
