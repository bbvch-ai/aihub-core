from llama_index.core.callbacks import TokenCountingHandler

from swiss_ai_hub.core.generative_ai.resources.costs.LLMCosts import LLMCosts


class LLMCostTracker:
    """
    Tracks token usage and costs for Large Language Model (LLM) operations (prompting, completion, embeddings).

    ### Why LLMCostTracker?
    When using LLM services, usage-based billing often depends on how many tokens are used in prompts, completions,
    and embeddings. The `LLMCostTracker` pairs with a `TokenCountingHandler` to:
    - Aggregate token counts across various operations.
    - Compute the associated costs given a price per 1000 tokens.

    By periodically retrieving total costs, developers can monitor and optimize their spending and usage.

    ### Key Points
    - **TokenCountingHandler Integration:** The `TokenCountingHandler` from `llama_index` tracks token usage.
      This class uses those counts and multiplies by per-thousand-token rates.
    - **Flexible Pricing:** Different models or vendors may charge different rates for prompts,
      completions, and embeddings. The constructor accepts costs per thousand tokens for each category.
    - **Cost Aggregation:** `get_total_costs()` returns a `LLMCosts` instance summarizing token usage and costs.

    ### Example
    ```python
    token_handler = TokenCountingHandler()
    cost_tracker = LLMCostTracker(
        token_counter=token_handler,
        prompt_tokens_costs_per_thousand=0.002,       # e.g., $0.002 per 1k prompt tokens
        completion_tokens_costs_per_thousand=0.002,   # e.g., same rate for completions
        embedding_tokens_costs_per_thousand=0.0005,   # cheaper for embeddings
    )

    # ... after some requests ...
    costs = cost_tracker.get_total_costs()
    print(costs)  # LLMCosts object with token counts and total cost
    ```

    """

    def __init__(
        self,
        token_counter: TokenCountingHandler,
        prompt_tokens_costs_per_thousand: float = 0,
        completion_tokens_costs_per_thousand: float = 0,
        embedding_tokens_costs_per_thousand: float = 0,
    ):
        self._token_counter = token_counter
        self._prompt_tokens_costs_per_thousand = prompt_tokens_costs_per_thousand
        self._completion_tokens_costs_per_thousand = completion_tokens_costs_per_thousand
        self._embedding_tokens_costs_per_thousand = embedding_tokens_costs_per_thousand

    def get_total_costs(self) -> LLMCosts:
        """
        Computes and returns the total token usage and corresponding costs so far.
        """
        return LLMCosts(
            prompt_token_count=self._token_counter.prompt_llm_token_count,
            completion_token_count=self._token_counter.completion_llm_token_count,
            embedding_token_count=self._token_counter.total_embedding_token_count,
            prompt_tokens_costs=(
                self._token_counter.prompt_llm_token_count * self._prompt_tokens_costs_per_thousand / 1000
            ),
            completion_tokens_costs=(
                self._token_counter.completion_llm_token_count * self._completion_tokens_costs_per_thousand / 1000
            ),
            embedding_tokens_costs=(
                self._token_counter.total_embedding_token_count * self._embedding_tokens_costs_per_thousand / 1000
            ),
        )
