from collections.abc import Callable
from typing import Annotated

import httpx
from llama_index.core.callbacks import TokenCountingHandler
from llama_index.core.utilities.token_counting import TokenCounter
from opentelemetry.propagate import inject
from pydantic import BaseModel, Field

from aihub_lib.generative_ai.resources.costs.LLMCostTracker import LLMCostTracker
from aihub_lib.generative_ai.resources.models.llm.LiteLLMBase import LiteLLMBase
from aihub_lib.infrastructure.litellm.LiteLLMProxySettings import LiteLLMProxySettings


class RerankingResult(BaseModel):
    """Result of reranking."""

    index: Annotated[int, Field(description="Index in the original list before reranking.")]
    text: Annotated[str, Field(description="The text to compare to the query.")]
    relevance_score: Annotated[float, Field(description="How relevant the text is to the query.")]


class RerankingLLMParameter(BaseModel):
    """Parameters specific to reranking models."""

    max_retries: Annotated[int, Field(description="Maximum number of retries.", ge=0)] = 10
    timeout: Annotated[float, Field(description="Timeout for each request.", ge=0)] = 60.0


class RerankingService(BaseModel):
    """
    Service wrapper for reranking operations using LiteLLM proxy.

    This service handles the actual HTTP communication with the LiteLLM proxy
    and abstracts away the low-level details. Similar to how OpenAILikeEmbedding
    works for embeddings.
    """

    model_name: Annotated[str, Field(description="")]
    api_base: Annotated[str, Field(description="")]
    api_key: Annotated[str, Field(description="")]
    max_retries: Annotated[int, Field(description="")]
    timeout: Annotated[float, Field(description="")]
    default_headers: Annotated[dict[str, str], Field(description="")]
    tokenizer: Annotated[Callable[[str], list[int]], Field(description="")]

    def _chunk_node(self, node: str, max_tokens: int) -> list[str]:
        """Chunk a node into smaller pieces that fit within token limits."""
        if not node.strip():
            return [node]

        token_counter = TokenCounter(self.tokenizer)
        tokens = token_counter.get_string_tokens(node)

        if tokens <= max_tokens:
            return [node]

        step_size = int(max_tokens * 0.75)
        words = node.split()
        chunks = [node[i : i + step_size] for i in range(0, len(words), step_size)]

        return chunks

    async def rerank(self, query: str, nodes: list[str], top_k: int, max_tokens: int) -> list[RerankingResult]:
        """Rerank documents using the configured reranking model."""

        all_results = []
        token_counter = TokenCounter(self.tokenizer)
        query_tokens = token_counter.get_string_tokens(query)
        max_chunk_tokens = max_tokens - query_tokens

        for idx, node in enumerate(nodes):
            chunks = self._chunk_node(node, max_tokens=max_chunk_tokens)

            async with httpx.AsyncClient(
                timeout=self.timeout,
                headers=self.default_headers,
            ) as client:
                response = await client.post(
                    f"{self.api_base}/rerank",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                        **self.default_headers,
                    },
                    json={
                        "model": self.model_name,
                        "query": query,
                        "documents": chunks,
                    },
                )
                response.raise_for_status()
                result = response.json()

                results = result.get("results", [])

                score = max([res.get("relevance_score", 0) for res in results])

                all_results.append(RerankingResult(index=idx, text="", relevance_score=score))

        all_results.sort(key=lambda x: x.relevance_score, reverse=True)

        final_results = all_results[:top_k]

        return final_results


class RerankingModelConfig(LiteLLMBase[RerankingService]):
    """Configuration for a reranking model."""

    model_name: Annotated[str, Field(description="Name of the reranking model.")]
    default_parameter: Annotated[
        RerankingLLMParameter,
        Field(
            description="Default parameters for the reranking model.",
        ),
    ] = RerankingLLMParameter()

    def to_llama_index(self) -> tuple[RerankingService, LLMCostTracker]:
        config = LiteLLMProxySettings()
        model_info = self.get_model_info()

        token_counter = TokenCountingHandler(tokenizer=self.token_counter)
        cost_tracker = LLMCostTracker(
            token_counter=token_counter,
            prompt_tokens_costs_per_thousand=model_info["model_info"]["input_cost_per_token"] * 1000,
            completion_tokens_costs_per_thousand=0,
        )

        default_headers = {}
        inject(default_headers)

        reranking_service = RerankingService(
            model_name=self.model_name,
            api_base=config.BASE_URL,
            api_key=config.API_KEY.get_secret_value(),
            max_retries=self.default_parameter.max_retries,
            timeout=self.default_parameter.timeout,
            default_headers=default_headers,
            tokenizer=self.token_counter,
        )

        return reranking_service, cost_tracker

    def get_reranking_service(self) -> RerankingService:
        """Get a configured reranking service instance."""
        reranking_service, _ = self.to_llama_index()
        return reranking_service
