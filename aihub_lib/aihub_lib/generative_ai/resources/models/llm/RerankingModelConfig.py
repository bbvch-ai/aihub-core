from typing import Annotated, Any

from llama_index.core.callbacks import CallbackManager, TokenCountingHandler
from opentelemetry.propagate import inject
from pydantic import BaseModel, Field

from aihub_lib.generative_ai.resources.costs.LLMCostTracker import LLMCostTracker
from aihub_lib.generative_ai.resources.models.llm.LiteLLMBase import LiteLLMBase
from aihub_lib.infrastructure.litellm.LiteLLMProxySettings import LiteLLMProxySettings


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

    async def rerank(
        self,
        query: str,
        documents: list[str],
        top_k: int,
    ) -> dict[str, Any]:
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
        import httpx

        # Handle batching to avoid exceeding the reranker's batch size limit
        batch_size = 32  # Maximum batch size for huggingface-reranking-inference
        all_results = []

        async with httpx.AsyncClient(
            timeout=self.timeout,
            headers=self.default_headers,
        ) as client:
            for i in range(0, len(documents), batch_size):
                batch_documents = documents[i:i + batch_size]
                batch_top_k = min(len(batch_documents), top_k - len(all_results))

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
                        "documents": batch_documents,
                        "top_n": batch_top_k,
                    }
                )
                response.raise_for_status()
                batch_result = response.json()

                batch_results = batch_result.get("results", [])

                # Adjust indices to account for the batch offset
                for result in batch_results:
                    result["index"] = result["index"] + i
                    all_results.append(result)

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