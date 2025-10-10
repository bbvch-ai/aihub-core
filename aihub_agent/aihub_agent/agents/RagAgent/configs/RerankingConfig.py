from typing import Annotated

from aihub_lib.generative_ai.resources.models.llm.RerankingModelConfig import (
    RerankingLLMParameter,
    RerankingModelConfig,
)
from pydantic import BaseModel, Field


class RerankingConfig(BaseModel):
    """Configuration for document reranking in RAG workflows."""

    enabled: Annotated[bool, Field(description="Enable reranking of retrieved documents")] = False
    reranking_model: Annotated[RerankingModelConfig, Field(description="Configuration for the reranking model")] = (
        RerankingModelConfig(model_name="local/reranker-cpu", default_parameter=RerankingLLMParameter(timeout=60.0))
    )
    top_k: Annotated[
        int,
        Field(description="Number of documents to return after reranking", ge=1, le=100),
    ] = 5
    max_tokens: Annotated[int, Field(description="Maximum number of tokens supported by the reranking model.")] = 512
