from typing import Annotated, Self

from pydantic import Field
from swiss_ai_hub.core.form.form import Form
from swiss_ai_hub.core.generative_ai import EmbeddingModelConfig, RerankingModelConfig


class AttachedFilesConfig(Form):
    """The models that pick the relevant sections of an attached file too large to fit the prompt whole."""

    embedding_model: Annotated[
        EmbeddingModelConfig,
        Field(
            description="Embeds the query and a file's sections to shortlist the ones closest to the question.",
            title="Embedding Model",
        ),
    ] = EmbeddingModelConfig(model_name="embedding/bge-m3")
    reranking_model: Annotated[
        RerankingModelConfig,
        Field(
            description="Orders the shortlisted sections by relevance before they fill the room left in the prompt.",
            title="Reranking Model",
        ),
    ] = RerankingModelConfig(model_name="reranker/bge")

    @classmethod
    def as_form(cls) -> Self:
        return cls(embedding_model=EmbeddingModelConfig.as_form(), reranking_model=RerankingModelConfig.as_form())
