from llama_index.core.callbacks import TokenCountingHandler

from lib_core.records.agent.Costs import Costs


class CostTracker:
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

    def get_total_costs(self) -> Costs:
        return Costs(
            prompt_token_count=self._token_counter.prompt_llm_token_count,
            completion_token_count=self._token_counter.completion_llm_token_count,
            embedding_token_count=self._token_counter.total_embedding_token_count,
            prompt_tokens_costs=self._token_counter.prompt_llm_token_count
            * self._prompt_tokens_costs_per_thousand
            / 1000,
            completion_tokens_costs=self._token_counter.completion_llm_token_count
            * self._completion_tokens_costs_per_thousand
            / 1000,
            embedding_tokens_costs=self._token_counter.total_embedding_token_count
            * self._embedding_tokens_costs_per_thousand
            / 1000,
        )
