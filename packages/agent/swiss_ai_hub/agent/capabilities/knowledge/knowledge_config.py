from typing import Annotated, Self

from pydantic import Field
from swiss_ai_hub.core.form.constraints import Ge
from swiss_ai_hub.core.form.form import Form
from swiss_ai_hub.core.generative_ai import RerankingModelConfig


class KnowledgeConfig(Form):
    """How the collections a user references are searched: the same for every collection, since nobody configured
    them for this agent. Each database is embedded with its own model; only the ranking is chosen here."""

    reranking_model: Annotated[
        RerankingModelConfig,
        Field(
            description="Orders what the referenced collections return and keeps the best of it for the prompt.",
            title="Reranking Model",
        ),
    ] = RerankingModelConfig(model_name="reranker/bge")
    retrieve_k: Annotated[
        int,
        Field(description="How many sections each referenced database returns before the reranker picks the best."),
        Ge(1),
    ] = 10
    tokens_per_section: Annotated[
        int,
        Field(
            description="A found section's size in tokens for reserving room, on the generous side: ingestion chunks "
            "are shorter, but headings and document metadata ride along with them."
        ),
        Ge(1),
    ] = 800

    def context_reserve(self) -> int:
        """Tokens to keep free for what the search returns, so attached files cannot crowd it out."""
        return self.reranking_model.top_n * self.tokens_per_section

    @classmethod
    def as_form(cls) -> Self:
        return cls(reranking_model=RerankingModelConfig.as_form())
