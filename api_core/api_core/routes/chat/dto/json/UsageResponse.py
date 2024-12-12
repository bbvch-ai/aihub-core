from pydantic import BaseModel, Field


class UsageResponse(BaseModel):
    """Represents token usage statistics for an API request."""

    prompt_tokens: int = Field(..., description="Number of tokens used in the prompt", example=50)
    completion_tokens: int = Field(..., description="Number of tokens used in the completion", example=100)
    total_tokens: int = Field(
        ...,
        description="Total number of tokens used in the request",
        example=150,
    )
