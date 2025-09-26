from typing import Annotated, Any, Callable

from llama_index.core.callbacks import TokenCountingHandler
from llama_index.core.utilities.token_counting import TokenCounter
from opentelemetry.propagate import inject
from pydantic import BaseModel, Field
import httpx
import logging
from aihub_lib.generative_ai.resources.costs.LLMCostTracker import LLMCostTracker
from aihub_lib.generative_ai.resources.models.llm.LiteLLMBase import LiteLLMBase
from aihub_lib.infrastructure.litellm.LiteLLMProxySettings import LiteLLMProxySettings


"""
{
    "id":"eb7bfb5d-a1bd-4cc0-9b8b-e8b612faf379",
    "results":
        [
            {"index":0,"relevance_score":0.996852},
            {"index":2,"relevance_score":0.2821962},
            {"index":1,"relevance_score":0.00003734357}
        ],
    "meta":
        {"api_version":{"version":"1.0"},"billed_units":{"search_units":1},"tokens":{"input_tokens":24,"output_tokens":50}}}%   (
"""


class RerankingLLMParameter(BaseModel):
    """
    Parameters specific to reranking models.

    ### Why RerankingLLMParameter?
    Reranking models may not have as many parameters as generative models, but by keeping a separate class,
    we maintain consistency with other model configs and facilitate extension if reranking models
    require additional parameters in the future.
    """

    max_retries: int = Field(default=10, description="Maximum number of retries.", ge=0)
    timeout: float = Field(default=60.0, description="Timeout for each request.", ge=0)


class RerankingService(BaseModel):
    """
    Service wrapper for reranking operations using LiteLLM proxy.

    This service handles the actual HTTP communication with the LiteLLM proxy
    and abstracts away the low-level details. Similar to how OpenAILikeEmbedding
    works for embeddings.
    """

    model_name: str
    api_base: str
    api_key: str
    max_retries: int
    timeout: float
    default_headers: dict[str, str]
    tokenizer: Callable[[str], list[int]]

    def _chunk_document(self, document: str, max_tokens: int = 30) -> list[str]:
        """
        Chunk a document into smaller pieces that fit within token limits.

        Uses proper token counting with word-based chunking and overlap to ensure
        we don't lose context while staying strictly under the token limit.
        """
        if not document.strip():
            return [document]

        token_counter = TokenCounter(self.tokenizer)
        tokens = token_counter.get_string_tokens(document)

        if tokens <= max_tokens:
            return [document]

        word_count = int(max_tokens * 0.75)
        words = document.split()
        chunks = [document[i : i + word_count] for i in range(0, len(words), word_count)]

        return chunks

    async def rerank(self, query: str, documents: list[str], top_k: int, max_tokens: int) -> dict[str, Any]:
        """
        Rerank documents using the configured reranking model.

        Handles batching internally to avoid exceeding service batch size limits.

        Args:
            query: The search query
            documents: List of document texts to rerank
            top_k: Number of top documents to return

        Returns:
            Dictionary with reranking results from LiteLLM
        """

        # Handle batching to avoid exceeding the reranker's batch size limit
        batch_size = 32  # Maximum batch size for huggingface-reranking-inference
        all_results = []
        token_counter = TokenCounter(self.tokenizer)
        query_tokens = token_counter.get_string_tokens(query)
        max_chunk_tokens = max_tokens - query_tokens

        for idx, document in enumerate(documents):
            chunks = self._chunk_document(document, max_tokens=max_chunk_tokens)

            async with httpx.AsyncClient(
                timeout=self.timeout,
                headers=self.default_headers,
            ) as client:
                for i in range(0, len(chunks), batch_size):
                    batch_chunks = chunks[i : i + batch_size]
                    batch_top_k = min(len(batch_chunks), top_k - len(all_results))

                    if batch_top_k <= 0:
                        break

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
                            "documents": batch_chunks,
                            "top_n": batch_top_k,
                        },
                    )
                    response.raise_for_status()
                    batch_result = response.json()

                    batch_results = batch_result.get("results", [])

                    score = max([batch_result.get("relevance_score", 0) for batch_result in batch_results])

                    all_results.append({"index": idx, "relevance_score": score})

        # Sort all results by score (descending) and take top_k
        all_results.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
        final_results = all_results[:top_k]

        # Return in the same format as the original service
        return {"results": final_results}


class RerankingModelConfig(LiteLLMBase[RerankingService]):
    """
    Configuration for a reranking model.

    ### Why RerankingModelConfig?
    Reranking models produce relevance scores for document-query pairs. They may have different endpoints
    and possibly fewer parameters compared to chat models. This config ensures each reranking
    model can be integrated uniformly with cost tracking and proper configuration management.
    """

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
            completion_tokens_costs_per_thousand=0,  # Reranking typically doesn't have completion tokens
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
        """
        Get a configured reranking service instance.

        This is the preferred way to get a reranking service, following
        the same pattern as EmbeddingModelConfig.
        """
        reranking_service, _ = self.to_llama_index()
        return reranking_service
