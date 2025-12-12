from typing import Annotated

from pydantic import BaseModel, Field


class UpdateMemoryResponse(BaseModel):
    """Response for updating a memory."""

    status: Annotated[
        str, Field(description="Operation status. Always 'updated' on success; errors raise HTTPException.")
    ]
    memory_id: Annotated[str, Field(description="ID of the memory that was updated. Echoed from request path.")]
