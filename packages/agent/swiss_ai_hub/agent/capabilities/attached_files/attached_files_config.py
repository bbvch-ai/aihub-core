from typing import Annotated, Self

from pydantic import Field
from swiss_ai_hub.core.form.constraints import Ge, Gt, Le
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
    share_of_input_budget: Annotated[
        float,
        Field(
            description="Share of the room left after the history that the files may fill, so the other context blocks "
            "(memory, later web content) always keep some."
        ),
        Gt(0.0),
        Le(1.0),
    ] = 0.8
    shortlist_size: Annotated[
        int,
        Field(
            description="How many sections, closest to the query by embedding, the reranker orders. The reranker is "
            "the slower and better judge, so it sees a shortlist rather than every section of a long file."
        ),
        Ge(1),
    ] = 40

    @classmethod
    def as_form(cls) -> Self:
        defaults = cls()
        return cls(
            embedding_model=EmbeddingModelConfig.as_form(defaults.embedding_model.model_name),
            reranking_model=RerankingModelConfig.as_form(defaults.reranking_model.model_name),
        )
