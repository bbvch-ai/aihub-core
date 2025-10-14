from collections.abc import Callable
from typing import Annotated

import httpx
from llama_index.core.callbacks import TokenCountingHandler
from llama_index.core.utilities.token_counting import TokenCounter
from llama_index.postprocessor.cohere_rerank import CohereRerank
from opentelemetry.propagate import inject
from pydantic import BaseModel, Field

from aihub_lib.generative_ai.resources.costs.LLMCostTracker import LLMCostTracker
from aihub_lib.generative_ai.resources.models.llm.LiteLLMBase import LiteLLMBase
from aihub_lib.infrastructure.litellm.LiteLLMProxySettings import LiteLLMProxySettings


# TODO Split into seperate files


class RerankingResult(BaseModel):
    """Result of reranking."""

    index: Annotated[int, Field(description="Index in the original list before reranking.")]
    text: Annotated[str, Field(description="The text to compare to the query.")]
    relevance_score: Annotated[float, Field(description="How relevant the text is to the query.")]


class RerankingLLMParameter(BaseModel):
    """Parameters specific to reranking models."""

    max_retries: Annotated[int, Field(description="Maximum number of retries.", ge=0)] = 10
    timeout: Annotated[float, Field(description="Timeout for each request.", ge=0)] = 60.0


# TODO use CohereRerank, take inspiration from prev next implementation using llama index (VectorPrevNextPostProcessor)
class RerankingService(BaseModel):
    """"""

    model_name: Annotated[str, Field(description="")]
    api_key: Annotated[str, Field(description="")]
    top_p: Annotated[int, Field(description="")]

    def _chunk_node(self, node: str, max_tokens: int) -> list[str]:
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

    async def rerank(
        self, query: str, nodes: list[str], top_k: int, max_tokens: int, batch_size: int
    ) -> list[RerankingResult]:

        all_results = []
        token_counter = TokenCounter(self.tokenizer)
        query_tokens = token_counter.get_string_tokens(query)
        max_chunk_tokens = max_tokens - query_tokens

        for idx, node in enumerate(nodes):
            chunks = self._chunk_node(node, max_tokens=max_chunk_tokens)
            results = []
            for i in range(0, len(chunks), batch_size):
                chunks_iter = chunks[i : i + batch_size]
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
                            "documents": chunks_iter,
                        },
                    )
                    response.raise_for_status()
                    result = response.json()

                    results.extend(result.get("results", []))

                score = max([res.get("relevance_score", 0) for res in results])

                all_results.append(RerankingResult(index=idx, text="", relevance_score=score))

        all_results.sort(key=lambda x: x.relevance_score, reverse=True)

        final_results = all_results[:top_k]

        return final_results


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

        default_headers = {}
        inject(default_headers)

        reranking_service = CohereRerank(
            model=self.model_name, api_key=config.API_KEY.get_secret_value(), base_url=config.BASE_URL, top_n=self.top_n
        )

        return reranking_service, cost_tracker
