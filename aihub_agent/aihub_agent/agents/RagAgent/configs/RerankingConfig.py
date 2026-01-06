from typing import Annotated, Any

from aihub_lib.generative_ai.resources.models.llm.RerankingModelConfig import (
    RerankingModelConfig,
)
from pydantic import BaseModel, Field, field_validator, model_validator


class RerankingConfig(BaseModel):
    """Configuration for document reranking in RAG workflows."""

    enabled: Annotated[bool, Field(description="Enable reranking of retrieved documents")] = False
    reranking_model: Annotated[
        RerankingModelConfig | None, Field(description="Configuration for the reranking model")
    ] = None

    @field_validator("reranking_model", mode="before")
    @classmethod
    def empty_dict_to_none(cls, v: Any) -> Any:
        """Convert empty dict from FormKit to None."""
        if isinstance(v, dict) and not v:
            return None
        return v

    @model_validator(mode="after")
    def validate_reranking_model_required_when_enabled(self) -> "RerankingConfig":
        if self.enabled and self.reranking_model is None:
            raise ValueError("reranking_model must be provided when reranking is enabled.")
        return self
