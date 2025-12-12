from typing import Annotated

from pydantic import BaseModel, Field


class DeleteMemoryResponse(BaseModel):
    """Response for deleting a single memory."""

    status: Annotated[
        str, Field(description="Operation status. Always 'deleted' on success; errors raise HTTPException.")
    ]
    memory_id: Annotated[str, Field(description="ID of the memory that was deleted. Echoed from request path.")]


class DeleteAllMemoriesResponse(BaseModel):
    """Response for deleting all memories."""

    status: Annotated[
        str, Field(description="Operation status. Always 'deleted_all' on success; errors raise HTTPException.")
    ]
