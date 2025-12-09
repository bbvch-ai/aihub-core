from typing import Annotated, Literal

from llama_index.core.vector_stores.types import VectorStoreQueryMode
from pydantic import BaseModel, Field

from aihub_lib.generative_ai.processors.models.RetrievePrevNextConfig import RetrievePrevNextConfig
from aihub_lib.generative_ai.resources.models.llm.EmbeddingModelConfig import EmbeddingModelConfig
from aihub_lib.generative_ai.retrievers.BaseRetrieverConfig import BaseRetrieverConfig, RetrieverType
from aihub_lib.persistence.rag.vectors.stores.MilvusVectorStoreConfig import MilvusVectorStoreConfig


class RetrieveSummariesConfig(BaseModel):
    """Configuration for retrieving parent summary nodes."""

    max_parent_levels: Annotated[
        int, Field(description="Maximum number of parent levels to retrieve summaries from.")
    ] = 2


class KnowledgeRetrieverConfig(BaseRetrieverConfig):
    """Configuration for retrieving knowledge from a vector store (Milvus)."""

    retriever_type: Literal[RetrieverType.KNOWLEDGE] = RetrieverType.KNOWLEDGE

    embed_model: Annotated[EmbeddingModelConfig, Field(description="The embedding model configuration.")]
    vector_store: Annotated[MilvusVectorStoreConfig, Field(description="The vector store configuration.")]
    index_namespaces: Annotated[list[str], Field(description="The namespaces to retrieve from.", min_length=1)]
    retrieve_k: Annotated[int, Field(description="The number of documents to retrieve.", ge=1)]
    query_mode: Annotated[
        VectorStoreQueryMode,
        Field(description="Specifies how the vector store should be queried (e.g., 'default', 'hybrid')."),
    ] = VectorStoreQueryMode.DEFAULT
    node_types: Annotated[
        list[Literal["summary", "content"]],
        Field(description="The types of nodes to retrieve (options: 'summary' or 'content').", min_length=1),
    ] = ["content"]
    retrieve_prev_next: Annotated[
        RetrievePrevNextConfig | None,
        Field(description="Configuration for retrieving previous and next nodes."),
    ] = None
    retrieve_summaries: Annotated[
        RetrieveSummariesConfig | None,
        Field(description="Configuration for retrieving parent summary nodes."),
    ] = None
