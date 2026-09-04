import os
from typing import Annotated

from mem0.configs.base import MemoryConfig
from mem0.configs.rerankers.config import RerankerConfig
from mem0.embeddings.configs import EmbedderConfig
from mem0.graphs.configs import GraphStoreConfig, Neo4jConfig
from mem0.llms.configs import LlmConfig
from mem0.vector_stores.configs import VectorStoreConfig
from pydantic import Field

from swiss_ai_hub.core.generative_ai.document.parsers.markdown_structural_node_parser import (
    DEFAULT_EMBEDDING_MAX_INPUT_TOKENS,
    EMBEDDING_BUDGET_SAFETY_FACTOR,
)
from swiss_ai_hub.core.infrastructure.litellm.lite_llm_proxy_settings import LiteLLMProxySettings
from swiss_ai_hub.core.infrastructure.milvus.milvus_settings import MilvusSettings
from swiss_ai_hub.core.infrastructure.neo4j.neo4j_settings import Neo4jSettings
from swiss_ai_hub.core.settings.environment_settings import EnvironmentSettings


class Mem0Settings(EnvironmentSettings):
    model_config = EnvironmentSettings.create_settings_config("MEM0_")
    LLM_NAME: Annotated[str, Field(description="Name of the LLM to use")]
    EMBEDDING_MODEL_NAME: Annotated[str, Field(description="Name of the embedding model to use")]
    RERANKING_MODEL_NAME: Annotated[str, Field(description="Name of the embedding model to use")]

    SUPPORT_VISION: Annotated[bool, Field(description="Whether to support vision")] = True
    VISION_DETAIL: Annotated[str, Field(description="Vision details")] = "auto"
    EMBEDDING_MAX_INPUT_TOKENS: Annotated[
        int | None,
        Field(description="Maximum number of tokens accepted by the configured embedding model", gt=0),
    ] = None

    def resolved_embedding_max_input_tokens(self) -> int:
        if self.EMBEDDING_MAX_INPUT_TOKENS is not None:
            return self.EMBEDDING_MAX_INPUT_TOKENS

        response_data = LiteLLMProxySettings().httpx_client.get("/v1/model/info").json()
        models = response_data.get("data", []) if isinstance(response_data, dict) else []
        model = next(
            (
                entry
                for entry in models
                if isinstance(entry, dict) and entry.get("model_name") == self.EMBEDDING_MODEL_NAME
            ),
            None,
        )
        model_info = model.get("model_info") if model else None
        max_input_tokens = model_info.get("max_input_tokens") if isinstance(model_info, dict) else None
        if max_input_tokens:
            return max(1, int(max_input_tokens * EMBEDDING_BUDGET_SAFETY_FACTOR))
        return int(DEFAULT_EMBEDDING_MAX_INPUT_TOKENS * EMBEDDING_BUDGET_SAFETY_FACTOR)

    def get_config(
        self,
        custom_fact_extraction_prompt: Annotated[str | None, "How LLM extracts facts from conversations"] = None,
        custom_update_memory_prompt: Annotated[str | None, "How LLM decides to ADD/UPDATE/DELETE memories"] = None,
        enable_graph: Annotated[bool, "Include the Neo4j graph store. When False, mem0 skips the graph branch."] = True,
    ) -> MemoryConfig:
        litellm = LiteLLMProxySettings()
        milvus = MilvusSettings()
        neo4j = Neo4jSettings()
        os.environ["CO_API_URL"] = litellm.BASE_URL
        graph_store = (
            GraphStoreConfig(
                provider="neo4j",
                config=Neo4jConfig(
                    url=neo4j.URL,
                    username=neo4j.USERNAME,
                    password=neo4j.PASSWORD.get_secret_value(),
                    base_label=False,
                ),
            )
            if enable_graph
            # Empty GraphStoreConfig → mem0 sets enable_graph=False and skips the graph branch (base.py: it
            # keys enable_graph on graph_store.config being truthy). The field is non-Optional, so pass an
            # empty config rather than None.
            else GraphStoreConfig()
        )
        return MemoryConfig(
            custom_fact_extraction_prompt=custom_fact_extraction_prompt,
            custom_update_memory_prompt=custom_update_memory_prompt,
            llm=LlmConfig(
                provider="openai",
                config={
                    "model": self.LLM_NAME,
                    "temperature": 0.2,
                    "max_tokens": 16_000,
                    "api_key": litellm.API_KEY.get_secret_value(),
                    "openai_base_url": litellm.BASE_URL,
                    "enable_vision": self.SUPPORT_VISION,
                    "vision_details": self.VISION_DETAIL,
                },
            ),
            embedder=EmbedderConfig(
                provider="openai",
                config={
                    "model": self.EMBEDDING_MODEL_NAME,
                    "api_key": litellm.API_KEY.get_secret_value(),
                    "openai_base_url": litellm.BASE_URL,
                },
            ),
            vector_store=VectorStoreConfig(
                provider="milvus",
                config={
                    "url": milvus.URL,
                    "token": milvus.get_token(),
                    "db_name": "default",
                    "collection_name": "memories",
                    "embedding_model_dims": milvus.DIMENSION,
                    "metric_type": "COSINE",
                },
            ),
            reranker=RerankerConfig(
                provider="cohere",
                config={
                    "model": self.RERANKING_MODEL_NAME,
                    "api_key": litellm.API_KEY.get_secret_value(),
                    "top_k": 20,
                    "return_documents": False,
                    "max_chunks_per_doc": None,
                },
            ),
            graph_store=graph_store,
        )
