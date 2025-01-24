from typing import List, Literal

from llama_index.core.vector_stores.types import VectorStoreQueryMode, BasePydanticVectorStore
from pydantic import Field

from aihub_lib.generative_ai.agent.AgentConfig import StepConfig
from aihub_lib.generative_ai.llms.models.embedding.azure.AzureOpenAIEmbeddingConfig import AzureOpenAIEmbeddingConfig
from aihub_lib.generative_ai.llms.models.embedding.self_hosted.SelfHostedEmbeddingConfig import (
    SelfHostedEmbeddingConfig,
)


class RetrieveStepConfig(StepConfig):
    """
    Configuration for the step retrieving documents from a vector store.
    """

    embed_model: AzureOpenAIEmbeddingConfig | SelfHostedEmbeddingConfig = Field(
        ..., description="The embedding model configuration."
    )
    index_namespaces: List[str] = Field(..., description="The namespaces to retrieve from.", min_length=1)
    retrieve_k: int = Field(..., description="The number of documents to retrieve.", ge=1)
    query_mode: VectorStoreQueryMode = Field(
        ..., description="Specifies how the vector store should be queried (e.g., 'default', 'hybrid')."
    )
    node_types: List[Literal["summary", "content"]] = Field(
        ..., description="The types of nodes to retrieve (options: 'summary' or 'content').", min_length=1
    )
    vector_store: BasePydanticVectorStore = Field(..., description="The vector store to retrieve from.")
