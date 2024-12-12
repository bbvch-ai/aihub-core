from pydantic import BaseModel, Field


class LLMCosts(BaseModel):
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

    @classmethod
    def from_zero(cls):
        return cls(
            prompt_token_count=0,
            completion_token_count=0,
            embedding_token_count=0,
            prompt_tokens_costs=0,
            completion_tokens_costs=0,
            embedding_tokens_costs=0,
        )

    def __add__(self, other):
        return LLMCosts(
            prompt_token_count=self.prompt_token_count + other.prompt_token_count,
            completion_token_count=self.completion_token_count + other.completion_token_count,
            embedding_token_count=self.embedding_token_count + other.embedding_token_count,
            prompt_tokens_costs=self.prompt_tokens_costs + other.prompt_tokens_costs,
            completion_tokens_costs=self.completion_tokens_costs + other.completion_tokens_costs,
            embedding_tokens_costs=self.embedding_tokens_costs + other.embedding_tokens_costs,
        )