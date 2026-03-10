from typing import Annotated, ClassVar

from pydantic import Field

from swiss_ai_hub.core.generative_ai.resources.costs.LLMCosts import LLMCosts
from swiss_ai_hub.core.i18n.LocaleString import LocaleString
from swiss_ai_hub.core.nats.events.cost.CostEvent import CostEvent


class LLMCostEvent(CostEvent, LLMCosts):
    """
    A concrete event representing the costs associated with Large Language Model operations,
    including prompt, completion, and embedding token usage.

    ### Why LLMCostEvent?
    For teams tracking expenditures on LLM services, LLMCostEvent provides a direct, user-visible
    breakdown of the costs per run. As a display event, it can be surfaced in UIs or logs to give
    engineers, product managers, or finance teams clear insights into where tokens - and money - are
    going.
    """

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.llm_cost_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.llm_cost_event.description")
    llm_name: Annotated[
        str, Field(description="The name of the LLM service (e.g., 'openai/gpt-4') this event pertains to.")
    ]

    def get_total_costs(self) -> float:
        """Computes the sum of prompt, completion, and embedding costs, providing
        a straightforward measure of the total expenditure for a given run."""
        return self.prompt_tokens_costs + self.completion_tokens_costs + self.embedding_tokens_costs

    @classmethod
    def from_llm_costs(cls, llm_name: str, costs: LLMCosts):
        """
        Constructs an LLMCostEvent from a given LLMCosts object and an LLM name.
        This allows for easy conversion from generic cost tracking logic to a user-facing event.
        """
        return cls(
            llm_name=llm_name,
            prompt_token_count=costs.prompt_token_count,
            completion_token_count=costs.completion_token_count,
            embedding_token_count=costs.embedding_token_count,
            prompt_tokens_costs=costs.prompt_tokens_costs,
            completion_tokens_costs=costs.completion_tokens_costs,
            embedding_tokens_costs=costs.embedding_tokens_costs,
        )
