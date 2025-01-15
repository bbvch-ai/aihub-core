from typing import List, Literal

from aihub_lib.generative_ai.agent.AgentConfig import StepConfig
from aihub_lib.generative_ai.llms.models.embedding.azure.AzureOpenAIEmbeddingConfig import AzureOpenAIEmbeddingConfig
from llama_index.core.vector_stores.types import VectorStoreQueryMode
from pydantic import Field


class RetrieveStepConfig(StepConfig):
    embed_model: AzureOpenAIEmbeddingConfig = Field(..., description="The embedding model configuration.")
    index_name: str = Field(..., description="The name of the index to retrieve from.")
    index_namespaces: List[str] = Field(..., description="The namespaces to retrieve from.", min_length=1)
    retrieve_k: int = Field(..., description="The number of documents to retrieve.", ge=1)
    query_mode: VectorStoreQueryMode = Field(..., description="The query mode to use.")
    node_types: List[Literal["summary", "content"]] = Field(
        ..., description="The types of nodes to retrieve. Allowed values are 'summary' and 'content'.", min_length=1
    )
