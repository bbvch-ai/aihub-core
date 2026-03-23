from typing import Annotated, Self

from pydantic import BaseModel, Field


class LLMCosts(BaseModel):
    """
    Represents the token usage and associated costs for different LLM operations (prompt, completion, embeddings).

    ### Why LLMCosts?
    When working with LLM services, you often need to track how many tokens are used and how that usage translates
    into cost. LLMCosts provides a structured representation of both token counts and computed monetary costs.

    ### Example
    ```python
    c1 = LLMCosts(
        prompt_token_count=1000,
        completion_token_count=500,
        embedding_token_count=300,
        prompt_tokens_costs=0.002,
        completion_tokens_costs=0.001,
        embedding_tokens_costs=0.00015,
    )

    c2 = LLMCosts.from_zero()  # zero costs
    total = c1 + c2  # total is the same as c1 in this case
    ```
    """

    prompt_token_count: Annotated[int, Field(description="Number of tokens used in the prompt")]
    completion_token_count: Annotated[
        int,
        Field(
            description="Number of tokens generated in the completion",
        ),
    ]
    embedding_token_count: Annotated[int, Field(description="Number of tokens used for embeddings")]
    prompt_tokens_costs: Annotated[float, Field(description="Cost associated with the prompt tokens")]
    completion_tokens_costs: Annotated[
        float,
        Field(
            description="Cost associated with the completion tokens",
        ),
    ]
    embedding_tokens_costs: Annotated[
        float,
        Field(
            description="Cost associated with the embedding tokens",
        ),
    ]

    @classmethod
    def from_zero(cls) -> Self:
        """Return an LLMCosts instance with all counts and costs set to zero."""
        return cls(
            prompt_token_count=0,
            completion_token_count=0,
            embedding_token_count=0,
            prompt_tokens_costs=0,
            completion_tokens_costs=0,
            embedding_tokens_costs=0,
        )

    def __add__(self, other: "LLMCosts") -> Self:
        """Allow aggregation of two LLMCosts objects by adding their fields."""
        return LLMCosts(
            prompt_token_count=self.prompt_token_count + other.prompt_token_count,
            completion_token_count=self.completion_token_count + other.completion_token_count,
            embedding_token_count=self.embedding_token_count + other.embedding_token_count,
            prompt_tokens_costs=self.prompt_tokens_costs + other.prompt_tokens_costs,
            completion_tokens_costs=self.completion_tokens_costs + other.completion_tokens_costs,
            embedding_tokens_costs=self.embedding_tokens_costs + other.embedding_tokens_costs,
        )
