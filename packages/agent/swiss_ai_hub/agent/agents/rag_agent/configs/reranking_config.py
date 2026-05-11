from typing import Annotated, Any, Self

from pydantic import Field, field_validator
from swiss_ai_hub.core.form.form import Form
from swiss_ai_hub.core.generative_ai import RerankingModelConfig


class RerankingConfig(Form):
    """
    Configuration for document reranking in RAG workflows.

    Supports duality pattern for form rendering and data validation.
    """

    reranking_model: Annotated[
        RerankingModelConfig | None,
        Field(description="Configuration for the reranking model"),
    ] = None

    @field_validator("reranking_model", mode="before")
    @classmethod
    def incomplete_dict_to_none(cls, v: Any) -> Any:
        """Convert empty or incomplete dict from FormKit to None.

        When reranking is disabled, the form may still send partial data
        (e.g., {top_n: 5} without model_name). We convert such incomplete
        configs to None to allow validation to pass.
        """
        if v is None:
            return None
        if isinstance(v, dict):
            if not v:
                return None
            if "model_name" not in v or not v.get("model_name"):
                return None
        return v

    @classmethod
    def as_form(cls) -> Self:
        """Factory method to create a form-mode RerankingConfig."""
        return cls(
            reranking_model=RerankingModelConfig.as_form(),
        )
