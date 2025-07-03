from typing import Annotated

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from aihub_lib.generative_ai.resources.models.llm.embedding.azure.AzureOpenAIEmbeddingConfig import (
    AzureOpenAIEmbeddingConfig,
    AzureOpenAIEmbeddingParameter,
)


class EmbeddingModelConfig(BaseSettings):
    EMBEDDING_MODEL_NAME: Annotated[str, Field(description="Name of the embedding model")]
    EMBEDDING_MODEL_BASE_URL: Annotated[str, Field(description="Base URL for the embedding model")]
    EMBEDDING_MODEL_API_VERSION: Annotated[str, Field(description="API version for the embedding model")]
    EMBEDDING_MODEL_TOKEN_COST: Annotated[float, Field(description="Token cost per thousands")]

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def azure_config(self) -> AzureOpenAIEmbeddingConfig:
        return AzureOpenAIEmbeddingConfig(
            name=self.EMBEDDING_MODEL_NAME,
            base_url=self.EMBEDDING_MODEL_BASE_URL,
            api_version=self.EMBEDDING_MODEL_API_VERSION,
            embedding_tokens_costs_per_thousand=self.EMBEDDING_MODEL_TOKEN_COST,
            default_parameter=AzureOpenAIEmbeddingParameter(),
        )
