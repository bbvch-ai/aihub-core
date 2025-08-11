from typing import Annotated

from pydantic import Field
from pydantic_settings import BaseSettings


class PipelineRunnerSettings(BaseSettings):
    MODEL_SUI_URL: Annotated[str, Field(description="Model SUI URL", pattern="^https?://.+$")] = (
        "https://api.example.com"
    )
    MODEL_SUI_API_KEY: Annotated[str | None, Field(description="Azure OpenAI API Key", pattern="^[A-Za-z0-9]+$")] = None
    MODEL_EUR_URL: Annotated[str, Field(description="Model SUI URL", pattern="^https?://.+$")] = (
        "https://api.example.com"
    )
    MODEL_EUR_API_KEY: Annotated[str | None, Field(description="Azure OpenAI API Key", pattern="^[A-Za-z0-9]+$")] = None
    VECTOR_STORE_URI: Annotated[str, Field(description="Vector Store URI", pattern="^http://.+$")] = (
        "http://milvus-standalone:19530"
    )
