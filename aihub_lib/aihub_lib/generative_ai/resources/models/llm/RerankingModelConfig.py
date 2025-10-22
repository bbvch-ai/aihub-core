from typing import Annotated

from llama_index.core.callbacks import TokenCountingHandler
from llama_index.postprocessor.cohere_rerank import CohereRerank
from pydantic import Field

from aihub_lib.generative_ai.resources.costs.LLMCostTracker import LLMCostTracker
from aihub_lib.generative_ai.resources.models.llm.LiteLLMBase import LiteLLMBase
from aihub_lib.infrastructure.litellm.LiteLLMProxySettings import LiteLLMProxySettings


class RerankingModelConfig(LiteLLMBase):
    """Configuration for a reranking model."""

    top_n: Annotated[
        int,
        Field(description="Number of documents to return after reranking", ge=1, le=100),
    ] = 5

    def to_llama_index(self) -> tuple[CohereRerank, LLMCostTracker]:
        config = LiteLLMProxySettings()
        model_info = self.get_model_info()

        token_counter = TokenCountingHandler(tokenizer=self.token_counter)
        cost_tracker = LLMCostTracker(
            token_counter=token_counter,
            prompt_tokens_costs_per_thousand=model_info["model_info"]["input_cost_per_token"] * 1000,
            completion_tokens_costs_per_thousand=0,
        )

        reranking_service = CohereRerank(
            model=self.model_name, api_key=config.API_KEY.get_secret_value(), base_url=config.BASE_URL, top_n=self.top_n
        )

        return reranking_service, cost_tracker
