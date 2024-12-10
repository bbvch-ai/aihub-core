from lib_core.generative_ai.llms.costs.LLMCosts import LLMCosts
from lib_core.nats.events.cost.CostEvent import CostEvent


class LLMCostEvent(CostEvent, LLMCosts):
    model_name: str

    def get_total_costs(self) -> float:
        return self.prompt_tokens_costs + self.completion_tokens_costs + self.embedding_tokens_costs

    @classmethod
    def from_llm_costs(cls, model_name: str, costs: LLMCosts):
        return cls(
            model_name=model_name,
            prompt_token_count=costs.prompt_token_count,
            completion_token_count=costs.completion_token_count,
            embedding_token_count=costs.embedding_token_count,
            prompt_tokens_costs=costs.prompt_tokens_costs,
            completion_tokens_costs=costs.completion_tokens_costs,
            embedding_tokens_costs=costs.embedding_tokens_costs,
        )