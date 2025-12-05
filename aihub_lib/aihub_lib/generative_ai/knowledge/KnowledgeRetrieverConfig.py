"""Configuration for vector store based knowledge retrieval."""

from typing import Annotated, Literal

from llama_index.core.vector_stores.types import VectorStoreQueryMode
from pydantic import Field

from aihub_lib.generative_ai.knowledge.BaseRetrieverConfig import BaseRetrieverConfig
from aihub_lib.generative_ai.processors.models.RetrievePrevNextConfig import RetrievePrevNextConfig
from aihub_lib.generative_ai.resources.models.llm.EmbeddingModelConfig import EmbeddingModelConfig
from aihub_lib.persistence.rag.vectors.stores.MilvusVectorStoreConfig import MilvusVectorStoreConfig


class KnowledgeRetrieverConfig(BaseRetrieverConfig):
    """
    Configuration for vector store based knowledge retrieval.

    Uses semantic search via embeddings stored in Milvus to find
    relevant document chunks based on query similarity.
    """

    retriever_type: Literal["knowledge"] = "knowledge"

    embed_model: Annotated[
        EmbeddingModelConfig,
        Field(description="The embedding model configuration."),
    ]
    vector_store: Annotated[
        MilvusVectorStoreConfig,
        Field(description="The vector store to retrieve from."),
    ]
    index_namespaces: Annotated[
        list[str],
        Field(description="The namespaces to retrieve from.", min_length=1),
    ]
    retrieve_k: Annotated[
        int,
        Field(description="The number of documents to retrieve.", ge=1),
    ]
    query_mode: Annotated[
        VectorStoreQueryMode,
        Field(description="Vector store query mode (default, hybrid, semantic_hybrid)."),
    ]
    node_types: Annotated[
        list[Literal["summary", "content"]],
        Field(description="Node types to retrieve (summary, content).", min_length=1),
    ]
    retrieve_prev_next: Annotated[
        RetrievePrevNextConfig | None,
        Field(description="Config for retrieving adjacent nodes."),
    ] = None
