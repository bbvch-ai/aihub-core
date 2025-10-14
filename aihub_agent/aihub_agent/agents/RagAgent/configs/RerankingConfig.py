from typing import Annotated

from aihub_lib.generative_ai.resources.models.llm.RerankingModelConfig import (
    RerankingModelConfig,
)
from pydantic import BaseModel, Field


class RerankingConfig(BaseModel):
    """Configuration for document reranking in RAG workflows."""

    enabled: Annotated[bool, Field(description="Enable reranking of retrieved documents")] = False
    reranking_model: Annotated[
        RerankingModelConfig | None, Field(description="Configuration for the reranking model")
    ] = None
