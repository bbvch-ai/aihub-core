from typing import Annotated

import httpx
import openai
from pydantic import Field

from aihub_lib.settings.EnvironmentSettings import EnvironmentSettings


class LiteLLMProxySettings(EnvironmentSettings):
    model_config = EnvironmentSettings.create_settings_config("LITE_LLM_PROXY_")

    BASE_URL: Annotated[str, Field(description="The base URL of the model.")]
    API_KEY: Annotated[
        str | None,
        Field(description="API key for authentication. If not provided, other authentication methods will be used."),
    ] = None

    @property
    def httpx_client(self) -> httpx.Client:
        return httpx.Client(
            headers={"Authorization": f"Bearer {self.API_KEY}"},
            base_url=self.BASE_URL,
        )

    @property
    def httpx_aclient(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            headers={"Authorization": f"Bearer {self.API_KEY}"},
            base_url=self.BASE_URL,
        )

    @property
    def openai_client(self) -> openai.Client:
        return openai.Client(
            api_key=self.API_KEY,
            base_url=self.BASE_URL,
        )

    @property
    def openai_aclient(self) -> openai.AsyncClient:
        return openai.AsyncClient(
            api_key=self.API_KEY,
            base_url=self.BASE_URL,
        )