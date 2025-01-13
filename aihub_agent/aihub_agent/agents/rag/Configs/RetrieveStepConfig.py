from typing import List

from aihub_lib.generative_ai.agent.AgentConfig import StepConfig
from aihub_lib.generative_ai.llms.models.embedding.azure.AzureOpenAIEmbeddingConfig import AzureOpenAIEmbeddingConfig
from llama_index.core.vector_stores.types import VectorStoreQueryMode


class RetrieveStepConfig(StepConfig):
    embed_model: AzureOpenAIEmbeddingConfig
    index_name: str
    index_namespaces: List[str]
    retrieve_k: int
    query_mode: VectorStoreQueryMode
    node_types: List[str]
