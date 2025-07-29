from typing import Annotated

from pydantic import Field

from aihub_lib.settings.EnvironmentSettings import EnvironmentSettings


class LiteLLMProxySettings(EnvironmentSettings):
    model_config = EnvironmentSettings.create_settings_config("LITE_LLM_PROXY_")

    BASE_URL: Annotated[str, Field(description="The base URL of the model.")]
    API_KEY: Annotated[
        str | None,
        Field(description="API key for authentication. If not provided, other authentication methods will be used."),
    ] = None
