from typing import Annotated

from pydantic import BaseModel, Field

from aihub_lib.generative_ai.resources.models.llm.RerankingModelConfig import (
    RerankingModelConfig,
    RerankingLLMParameter,
)


class RerankingConfig(BaseModel):
    """
    Configuration for document reranking in RAG workflows.

    This config focuses on service-level parameters like whether reranking is enabled,
    how many documents to return, etc. The actual model configuration is handled
    by RerankingModelConfig in the lib layer.
    """

    enabled: Annotated[bool, Field(description="Enable reranking of retrieved documents")] = False
    reranking_model: Annotated[RerankingModelConfig, Field(description="Configuration for the reranking model")] = (
        RerankingModelConfig(model_name="local/reranker", default_parameter=RerankingLLMParameter(timeout=60.0))
    )
    top_k: Annotated[
        int,
        Field(description="Number of documents to return after reranking", ge=1, le=100),
    ] = 5
    max_tokens: Annotated[int, Field(description="Maximum number of tokens supported by the reranking model.")] = 512

    def get_reranking_service(self):
        """
        Get the configured reranking service from the model config.

        Returns:
            RerankingService instance ready for use
        """
        return self.reranking_model.get_reranking_service()
