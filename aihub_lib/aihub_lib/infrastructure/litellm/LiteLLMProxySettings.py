from typing import Annotated

import httpx
import openai
from pydantic import Field, SecretStr

from aihub_lib.settings.EnvironmentSettings import EnvironmentSettings


class LiteLLMProxySettings(EnvironmentSettings):
    model_config = EnvironmentSettings.create_settings_config("LITE_LLM_PROXY_")

    BASE_URL: Annotated[str, Field(description="The base URL of the model.")]
    API_KEY: Annotated[
        SecretStr | None,
        Field(description="API key for authentication. If not provided, other authentication methods will be used."),
    ] = None
    MASTER_KEY: Annotated[
        SecretStr | None,
        Field(description="Master key for administrative operations (user/key management)."),
    ] = None

    USER_MAX_BUDGET: Annotated[float | None, Field(description="Budget available to a user in one period")] = None
    USER_SOFT_BUDGET: Annotated[
        float | None, Field(description="Get alerts when user crosses given budget, doesn't block requests.")
    ] = None
    USER_MAX_PARALLEL_REQUESTS: Annotated[
        int | None,
        Field(
            description="Rate limit a user based on the number of parallel requests. "
            "Raises 429 error, if user's parallel requests > x."
        ),
    ] = None
    USER_TPM_LIMIT: Annotated[
        int | None, Field(description="Specify tpm limit for a given user (Tokens per minute)")
    ] = None
    USER_RPM_LIMIT: Annotated[
        int | None, Field(description="Specify rpm limit for a given user (Requests per minute)")
    ] = None
    USER_BUDGET_DURATION: Annotated[
        int | None,
        Field(
            description="Budget is reset at the end of specified duration. If not set, budget is never reset. "
            'You can set duration as seconds ("30s"), minutes ("30m"), hours ("30h"), days ("30d"), '
            'months ("1mo").'
        ),
    ] = None

    @property
    def httpx_client(self) -> httpx.Client:
        if self.API_KEY is None:
            raise ValueError(
                "LITE_LLM_PROXY_API_KEY environment variable is required but not set. "
                "Please set it in your .env file."
            )
        return httpx.Client(
            headers={"Authorization": f"Bearer {self.API_KEY.get_secret_value()}"},
            base_url=self.BASE_URL,
        )

    @property
    def httpx_aclient(self) -> httpx.AsyncClient:
        if self.API_KEY is None:
            raise ValueError(
                "LITE_LLM_PROXY_API_KEY environment variable is required but not set. "
                "Please set it in your .env file."
            )
        return httpx.AsyncClient(
            headers={"Authorization": f"Bearer {self.API_KEY.get_secret_value()}"},
            base_url=self.BASE_URL,
        )

    @property
    def openai_aclient(self) -> openai.AsyncClient:
        if self.API_KEY is None:
            raise ValueError(
                "LITE_LLM_PROXY_API_KEY environment variable is required but not set. "
                "Please set it in your .env file."
            )
        return openai.AsyncClient(
            api_key=self.API_KEY.get_secret_value(),
            base_url=self.BASE_URL,
        )

    @property
    def httpx_admin_client(self) -> httpx.Client:
        """HTTP client for administrative operations using master key."""
        if self.MASTER_KEY is None:
            raise ValueError(
                "LITE_LLM_PROXY_MASTER_KEY environment variable is required for administrative operations but not set. "
                "Please set it in your .env file (typically same value as LITELLM_MASTER_KEY)."
            )
        return httpx.Client(
            headers={"Authorization": f"Bearer {self.MASTER_KEY.get_secret_value()}"},
            base_url=self.BASE_URL,
        )

    @property
    def httpx_admin_aclient(self) -> httpx.AsyncClient:
        """Async HTTP client for administrative operations using master key."""
        if self.MASTER_KEY is None:
            raise ValueError(
                "LITE_LLM_PROXY_MASTER_KEY environment variable is required for administrative operations but not set. "
                "Please set it in your .env file (typically same value as LITELLM_MASTER_KEY)."
            )
        return httpx.AsyncClient(
            headers={"Authorization": f"Bearer {self.MASTER_KEY.get_secret_value()}"},
            base_url=self.BASE_URL,
        )
