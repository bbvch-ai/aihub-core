import os
from typing import Annotated

from pydantic import Field

from aihub_lib.infrastructure.litellm.LiteLLMProxySettings import LiteLLMProxySettings
from aihub_lib.infrastructure.milvus.MilvusSettings import MilvusSettings
from aihub_lib.infrastructure.neo4j.Neo4jSettings import Neo4jSettings
from aihub_lib.settings.EnvironmentSettings import EnvironmentSettings


class Mem0Settings(EnvironmentSettings):
    model_config = EnvironmentSettings.create_settings_config("MEM0_")
    LLM_NAME: Annotated[str, Field(description="Name of the LLM to use")]
    EMBEDDING_MODEL_NAME: Annotated[str, Field(description="Name of the embedding model to use")]
    RERANKING_MODEL_NAME: Annotated[str, Field(description="Name of the embedding model to use")]

    SUPPORT_VISION: Annotated[bool, Field(description="Whether to support vision")] = True
    VISION_DETAIL: Annotated[str, Field(description="Vision details")] = "auto"

    @property
    def config(self) -> dict:
        litellm = LiteLLMProxySettings()
        milvus = MilvusSettings()
        neo4j = Neo4jSettings()
        os.environ["CO_API_URL"] = litellm.BASE_URL
        return {
            "llm": {
                "provider": "openai",
                "config": {
                    "model": self.LLM_NAME,
                    "temperature": 0.2,
                    "max_tokens": 2000,
                    "api_key": litellm.API_KEY.get_secret_value(),
                    "openai_base_url": litellm.BASE_URL,
                    "enable_vision": self.SUPPORT_VISION,
                    "vision_details": self.VISION_DETAIL,
                },
            },
            "embedder": {
                "provider": "openai",
                "config": {
                    "model": self.EMBEDDING_MODEL_NAME,
                    "api_key": litellm.API_KEY.get_secret_value(),
                    "openai_base_url": litellm.BASE_URL,
                },
            },
            "vector_store": {
                "provider": "milvus",
                "config": {
                    "url": milvus.URL,
                    "token": "token",
                    "db_name": "default",
                    "collection_name": "memories",
                    "embedding_model_dims": milvus.DIMENSION,
                },
            },
            "reranker": {
                "provider": "cohere",
                "config": {
                    "model": self.RERANKING_MODEL_NAME,
                    "api_key": litellm.API_KEY.get_secret_value(),
                    "top_k": 20,
                    "return_documents": False,
                    "max_chunks_per_doc": None,
                },
            },
            "graph_store": {
                "provider": "neo4j",
                "config": {
                    "url": neo4j.URL,
                    "username": neo4j.USERNAME,
                    "password": neo4j.PASSWORD,
                    "database": "neo4j",
                },
                # "custom_prompt": "Please only capture people, organisations, and project links.",
            },
        }
