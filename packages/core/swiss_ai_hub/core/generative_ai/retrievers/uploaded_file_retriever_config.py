from typing import Annotated, Self

from pydantic import Field

from swiss_ai_hub.core.form.constraints import Ge
from swiss_ai_hub.core.form.elements.input_number import InputNumber
from swiss_ai_hub.core.generative_ai.resources.models.llm.embedding_model_config import EmbeddingModelConfig
from swiss_ai_hub.core.generative_ai.retrievers.base_retriever_config import BaseRetrieverConfig
from swiss_ai_hub.core.i18n.locale_string import LocaleString


class UploadedFileRetrieverConfig(BaseRetrieverConfig):
    """
    Configuration for retrieving from files the chat client indexed before forwarding them.

    The embedding model must be the one the client used: a query embedded by a different model lands in
    another vector space, where every similarity score is arbitrary rather than wrong in a visible way.

    ``retrieve_k`` counts per file, not per turn. Internal documents measure 5-16 chunks, so the default
    returns whole small documents instead of a window into them — the point of this retriever is that the
    user just attached exactly what they want read.
    """

    embed_model: Annotated[
        EmbeddingModelConfig,
        Field(description="The embedding model the chat client used to index the uploaded files."),
    ]
    retrieve_k: Annotated[
        int | InputNumber,
        Field(description="The number of chunks to retrieve per uploaded file."),
        Ge(1),
    ] = 16

    @classmethod
    def as_form(cls) -> Self:
        """Factory method to create a form-mode UploadedFileRetrieverConfig."""
        return cls(
            embed_model=EmbeddingModelConfig.as_form(),
            retrieve_k=InputNumber(
                label=LocaleString.from_i18n_path("lib.retriever.config.retrieve_k.label"),
                help=LocaleString.from_i18n_path("lib.retriever.config.retrieve_k.help"),
                min=1,
                max=100,
                step=1,
            ),
        )
