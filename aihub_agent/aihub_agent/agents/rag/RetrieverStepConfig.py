from aihub_lib.generative_ai.agent.AgentConfig import StepConfig
from aihub_lib.generative_ai.llms.models.embedding.azure.AzureOpenAIEmbeddingConfig import (
    AzureOpenAIEmbeddingConfig,
)
from aihub_lib.persistence.rag.vectors.node_metadata import NODE_TYPE_CONTENT
from llama_index.core.vector_stores.types import VectorStoreQueryMode
from mongoengine import StringField, ListField, IntField


class RetrieverStepConfig(StepConfig):
    embed_model: AzureOpenAIEmbeddingConfig
    index_name = StringField(required=True)
    index_namespaces = ListField(StringField(), required=True)
    retrieve_k = IntField(required=True, default=8)
    query_mode = StringField(required=False, default=VectorStoreQueryMode.HYBRID)
    node_types = ListField(StringField(), required=False, default=[NODE_TYPE_CONTENT])
