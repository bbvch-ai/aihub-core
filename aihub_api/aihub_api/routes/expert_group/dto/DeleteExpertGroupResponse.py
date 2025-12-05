from pydantic import BaseModel


class DeleteExpertGroupResponse(BaseModel):
    """Response model for successful expert group deletion."""

    success: bool = True
    message: str = "Expert group deleted successfully."
