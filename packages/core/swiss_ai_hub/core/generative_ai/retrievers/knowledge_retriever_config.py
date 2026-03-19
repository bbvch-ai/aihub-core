from typing import Annotated, Literal, Self

from llama_index.core.vector_stores.types import VectorStoreQueryMode
from pydantic import Field

from swiss_ai_hub.core.form.constraints import Ge, MinLen
from swiss_ai_hub.core.form.elements.input_number import InputNumber
from swiss_ai_hub.core.form.elements.multi_select import MultiSelect
from swiss_ai_hub.core.form.elements.select import Select
from swiss_ai_hub.core.form.elements.vector_store_input import VectorStoreInput
from swiss_ai_hub.core.generative_ai.processors.models.retrieve_prev_next_config import RetrievePrevNextConfig
from swiss_ai_hub.core.generative_ai.processors.models.retrieve_summaries_config import RetrieveSummariesConfig
from swiss_ai_hub.core.generative_ai.resources.models.llm.embedding_model_config import EmbeddingModelConfig
from swiss_ai_hub.core.generative_ai.retrievers.base_retriever_config import BaseRetrieverConfig
from swiss_ai_hub.core.i18n.locale_string import LocaleString
from swiss_ai_hub.core.persistence.rag.vectors.stores.milvus_vector_store_config import MilvusVectorStoreConfig


class KnowledgeRetrieverConfig(BaseRetrieverConfig):
    """
    Configuration for retrieving knowledge from a vector store (Milvus).

    Supports duality pattern for form rendering and data validation.
    """

    embed_model: Annotated[
        EmbeddingModelConfig,
        Field(description="The embedding model configuration."),
    ]
    vector_store: Annotated[
        MilvusVectorStoreConfig | VectorStoreInput,
        Field(description="The vector store configuration."),
    ]
    retrieve_k: Annotated[
        int | InputNumber,
        Field(description="The number of documents to retrieve."),
        Ge(1),
    ] = 5
    query_mode: Annotated[
        VectorStoreQueryMode | Select,
        Field(description="Specifies how the vector store should be queried (e.g., 'default', 'hybrid')."),
    ] = VectorStoreQueryMode.DEFAULT
    node_types: Annotated[
        list[Literal["summary", "content"]] | MultiSelect,
        Field(description="The types of nodes to retrieve (options: 'summary' or 'content')."),
        MinLen(1),
    ] = ["content"]
    retrieve_prev_next: Annotated[
        RetrievePrevNextConfig | None,
        Field(description="Configuration for retrieving previous and next nodes.", title="Retrieve Previous/Next"),
    ] = None
    retrieve_summaries: Annotated[
        RetrieveSummariesConfig | None,
        Field(description="Configuration for retrieving parent summary nodes.", title="Retrieve Summaries"),
    ] = None

    @classmethod
    def as_form(cls) -> Self:
        """Factory method to create a form-mode KnowledgeRetrieverConfig."""
        return cls(
            embed_model=EmbeddingModelConfig.as_form(),
            vector_store=VectorStoreInput(
                label=LocaleString.from_i18n_path("lib.vectorStore.label"),
                help=LocaleString.from_i18n_path("lib.vectorStore.help"),
            ),
            retrieve_k=InputNumber(
                label=LocaleString.from_i18n_path("lib.retriever.config.retrieve_k.label"),
                help=LocaleString.from_i18n_path("lib.retriever.config.retrieve_k.help"),
                min=1,
                max=100,
                step=1,
            ),
            query_mode=Select(
                label=LocaleString.from_i18n_path("lib.retriever.config.query_mode.label"),
                help=LocaleString.from_i18n_path("lib.retriever.config.query_mode.help"),
                options=[
                    {"label": "Default", "value": VectorStoreQueryMode.DEFAULT.value},
                    {"label": "Hybrid", "value": VectorStoreQueryMode.HYBRID.value},
                    {"label": "Sparse", "value": VectorStoreQueryMode.SPARSE.value},
                ],
                option_label="label",
                option_value="value",
            ),
            node_types=MultiSelect(
                label=LocaleString.from_i18n_path("lib.retriever.config.node_types.label"),
                help=LocaleString.from_i18n_path("lib.retriever.config.node_types.help"),
                options=[
                    {"label": "Content", "value": "content"},
                    {"label": "Summary", "value": "summary"},
                ],
                option_label="label",
                option_value="value",
            ),
            retrieve_prev_next=RetrievePrevNextConfig.as_form(),
            retrieve_summaries=RetrieveSummariesConfig.as_form(),
        )
