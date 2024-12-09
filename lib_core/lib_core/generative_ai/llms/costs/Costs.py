from pydantic import BaseModel, Field


class Costs(BaseModel):
    """
    Represents the token usage and associated costs for different components of an API request.
    """

    prompt_token_count: int = Field(..., description="Number of tokens used in the prompt")
    completion_token_count: int = Field(
        ...,
        description="Number of tokens generated in the completion",
    )
    embedding_token_count: int = Field(..., description="Number of tokens used for embeddings")
    prompt_tokens_costs: float = Field(..., description="Cost associated with the prompt tokens")
    completion_tokens_costs: float = Field(
        ...,
        description="Cost associated with the completion tokens",
    )
    embedding_tokens_costs: float = Field(
        ...,
        description="Cost associated with the embedding tokens",
    )
