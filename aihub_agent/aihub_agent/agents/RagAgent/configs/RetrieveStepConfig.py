from typing import List, Literal, Optional

from aihub_lib.agents.AgentConfig import StepConfig
from aihub_lib.generative_ai.processors.models.RetrievePrevNextConfig import RetrievePrevNextConfig
from aihub_lib.generative_ai.resources.models.llm.embedding.EmbeddingLLMConfig import EmbeddingLLMConfig
from llama_index.core.vector_stores.types import BasePydanticVectorStore, VectorStoreQueryMode
from pydantic import Field


class RetrieveStepConfig(StepConfig):
    """
    Configuration for the step retrieving documents from a vector store.
    """

    embed_model: EmbeddingLLMConfig = Field(..., description="The embedding model configuration.")
    index_namespaces: List[str] = Field(..., description="The namespaces to retrieve from.", min_length=1)
    retrieve_k: int = Field(..., description="The number of documents to retrieve.", ge=1)
    query_mode: VectorStoreQueryMode = Field(
        ..., description="Specifies how the vector store should be queried (e.g., 'default', 'hybrid')."
    )
    node_types: List[Literal["summary", "content"]] = Field(
        ..., description="The types of nodes to retrieve (options: 'summary' or 'content').", min_length=1
    )
    vector_store: BasePydanticVectorStore = Field(..., description="The vector store to retrieve from.")
    retrieve_prev_next: Optional[RetrievePrevNextConfig] = Field(
        default=None,
        description="Whether to retrieve previous and next nodes based on the retrieved nodes from the vector store.",
    )
