from typing import Annotated, Literal

from aihub_lib.agents.AgentConfig import StepConfig
from aihub_lib.generative_ai.processors.models.RetrievePrevNextConfig import RetrievePrevNextConfig
from aihub_lib.generative_ai.resources.models.llm.EmbeddingModelConfig import EmbeddingModelConfig
from aihub_lib.persistence.rag.vectors.stores.AzureAISearchVectorStoreConfig import AzureAISearchVectorStoreConfig
from aihub_lib.persistence.rag.vectors.stores.MilvusVectorStoreConfig import MilvusVectorStoreConfig
from llama_index.core.vector_stores.types import VectorStoreQueryMode
from pydantic import Field

from aihub_agent.agents.RagAgent.configs.RetrieveSummariesConfig import RetrieveSummariesConfig


class RetrieveStepConfig(StepConfig):
    """
    Configuration for the step retrieving documents from a vector store.
    """

    embed_model: Annotated[EmbeddingModelConfig, Field(description="The embedding model configuration.")]
    index_namespaces: Annotated[list[str], Field(description="The namespaces to retrieve from.", min_length=1)]
    retrieve_k: Annotated[int, Field(description="The number of documents to retrieve.", ge=1)]
    query_mode: Annotated[
        VectorStoreQueryMode,
        Field(description="Specifies how the vector store should be queried (e.g., 'default', 'hybrid')."),
    ]
    node_types: Annotated[
        list[Literal["summary", "content"]],
        Field(description="The types of nodes to retrieve (options: 'summary' or 'content').", min_length=1),
    ]
    vector_store: Annotated[
        AzureAISearchVectorStoreConfig | MilvusVectorStoreConfig,
        Field(description="The vector store to retrieve from."),
    ]
    retrieve_prev_next: Annotated[
        RetrievePrevNextConfig | None,
        Field(
            description="Whether to retrieve previous and next nodes "
            "based on the retrieved nodes from the vector store.",
        ),
    ] = None
    retrieve_summaries: Annotated[
        RetrieveSummariesConfig | None,
        Field(
            description="Configurations for retrieving the parent summaries, max number of summary levels",
        ),
    ] = None
