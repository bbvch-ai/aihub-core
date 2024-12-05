from pydantic import BaseModel, Field


class Costs(BaseModel):
    """
    Represents the token usage and associated costs for different components of an API request.
    """

    prompt_token_count: int = Field(
        ..., description="Number of tokens used in the prompt", example=100
    )
    completion_token_count: int = Field(
        ...,
        description="Number of tokens generated in the completion",
        example=50,
    )
    embedding_token_count: int = Field(
        ..., description="Number of tokens used for embeddings", example=200
    )
    prompt_tokens_costs: float = Field(
        ..., description="Cost associated with the prompt tokens", example=0.002
    )
    completion_tokens_costs: float = Field(
        ...,
        description="Cost associated with the completion tokens",
        example=0.003,
    )
    embedding_tokens_costs: float = Field(
        ...,
        description="Cost associated with the embedding tokens",
        example=0.001,
    )
