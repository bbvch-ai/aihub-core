from typing import Annotated, Literal

from llama_index.core.vector_stores.types import VectorStoreQueryMode
from pydantic import Field

from aihub_lib.agents.AgentConfig import StepConfig
from aihub_lib.generative_ai.processors.models.RetrievePrevNextConfig import RetrievePrevNextConfig
from aihub_lib.generative_ai.processors.models.RetrieveSummariesConfig import RetrieveSummariesConfig
from aihub_lib.generative_ai.resources.models.llm.EmbeddingModelConfig import EmbeddingModelConfig
from aihub_lib.persistence.rag.vectors.stores.MilvusVectorStoreConfig import MilvusVectorStoreConfig


class KnowledgeRetrievalStepConfig(StepConfig):
    """
    Step configuration for knowledge retrieval.

    Contains all settings needed for vector store retrieval:
    - Embedding model configuration
    - Vector store configuration
    - Default namespaces (can be overridden at runtime)
    - Retrieval parameters
    """

    embed_model: Annotated[EmbeddingModelConfig, Field(description="The embedding model configuration.")]
    vector_store: Annotated[MilvusVectorStoreConfig, Field(description="The vector store configuration.")]
    namespaces: Annotated[list[str], Field(description="Default namespaces to retrieve from.", min_length=1)]
    retrieve_k: Annotated[int, Field(description="The number of documents to retrieve.", ge=1)] = 10
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
