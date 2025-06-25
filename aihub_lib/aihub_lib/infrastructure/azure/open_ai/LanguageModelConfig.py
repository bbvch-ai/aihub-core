from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from aihub_lib.generative_ai.resources.models.llm.chat.azure.AzureOpenAILLMConfig import (
    AzureOpenAILLMConfig,
    AzureOpenAIParameter,
)


class LanguageModelConfig(BaseSettings):
    LANGUAGE_MODEL_NAME: str = Field(default="gpt-4o-mini", description="Name of the language model")
    LANGUAGE_MODEL_BASE_URL: str = Field(
        default="https://bbvihub-openai-sui.openai.azure.com/", description="Base URL for the language model"
    )
    LANGUAGE_MODEL_API_VERSION: str = Field(
        default="2025-01-01-preview", description="API version for the language model"
    )
    LANGUAGE_MODEL_COMPLETION_TOKEN_COST: float = Field(
        default=0.0004958, description="Completion token cost per thousands"
    )
    LANGUAGE_MODEL_PROMPT_TOKEN_COST: float = Field(default=0.00012393, description="Prompt token cost per thousands")
    LANGUAGE_MODEL_TEMPERATURE: float = Field(
        default=0.0, description="Temperature for the language model, 0.0 means deterministic output"
    )
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def azure_config(self) -> AzureOpenAILLMConfig:
        return AzureOpenAILLMConfig(
            name=self.LANGUAGE_MODEL_NAME,
            base_url=self.LANGUAGE_MODEL_BASE_URL,
            api_version=self.LANGUAGE_MODEL_API_VERSION,
            completion_tokens_costs_per_thousand=self.LANGUAGE_MODEL_COMPLETION_TOKEN_COST,
            prompt_tokens_costs_per_thousand=self.LANGUAGE_MODEL_PROMPT_TOKEN_COST,
            default_parameter=AzureOpenAIParameter(temperature=self.LANGUAGE_MODEL_TEMPERATURE),
        )
