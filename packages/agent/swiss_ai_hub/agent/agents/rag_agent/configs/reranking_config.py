from typing import Annotated, Self

from pydantic import Field
from swiss_ai_hub.core.form.form import Form
from swiss_ai_hub.core.generative_ai import RerankingModelConfig


class RerankingConfig(Form):
    """
    Configuration for document reranking in RAG workflows.

    Supports duality pattern for form rendering and data validation.
    """

    reranking_model: Annotated[
        RerankingModelConfig,
        Field(description="Configuration for the reranking model"),
    ]

    @classmethod
    def as_form(cls) -> Self:
        """Factory method to create a form-mode RerankingConfig."""
        return cls(
            reranking_model=RerankingModelConfig.as_form(),
        )
