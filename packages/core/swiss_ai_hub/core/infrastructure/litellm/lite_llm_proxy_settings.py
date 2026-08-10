import asyncio
import weakref
from collections.abc import Callable
from typing import Annotated, Any, ClassVar

import httpx
import openai
from pydantic import Field, SecretStr

from swiss_ai_hub.core.settings.environment_settings import EnvironmentSettings


class LiteLLMProxySettings(EnvironmentSettings):
    model_config = EnvironmentSettings.create_settings_config("LITE_LLM_PROXY_")

    _sync_clients: ClassVar[dict[str, httpx.Client]] = {}
    _async_clients: ClassVar[weakref.WeakKeyDictionary[asyncio.AbstractEventLoop, dict[str, Any]]] = (
        weakref.WeakKeyDictionary()
    )

    BASE_URL: Annotated[str, Field(description="The base URL of the model.")]
    API_KEY: Annotated[
        SecretStr | None,
        Field(description="API key for authentication. If not provided, other authentication methods will be used."),
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
    def authorization_header(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.API_KEY.get_secret_value()}"}

    @staticmethod
    def pooled_async_client[TClient](key: str, create: Callable[[], TClient]) -> TClient:
        """
        Return the process-wide client for `key`, creating it on first use.

        Keyed by event loop as well: a client's pooled connections belong to the loop that opened them, so
        one cached from another loop fails on reuse. The weak keys let a finished loop drop its clients.
        """
        loop_clients = LiteLLMProxySettings._async_clients.setdefault(asyncio.get_running_loop(), {})
        if key not in loop_clients:
            loop_clients[key] = create()
        return loop_clients[key]

    @classmethod
    async def aclose_pooled_clients(cls) -> None:
        """
        Close the clients pooled for the running loop, plus the process-wide sync client.

        Dropping them from the pools lets a later access rebuild them: a process that starts a second app on
        the same loop — the API test runners do — must not inherit closed clients.
        """
        for client in cls._async_clients.pop(asyncio.get_running_loop(), {}).values():
            if isinstance(client, httpx.AsyncClient):
                await client.aclose()
            else:
                await client.close()

        for sync_client in cls._sync_clients.values():
            sync_client.close()
        cls._sync_clients.clear()

    @property
    def httpx_client(self) -> httpx.Client:
        """
        Shared, and callers must not close it.

        A client owns a connection pool, so minting one per access throws away keep-alive and — since httpx
        clients have no finaliser — leaks the pool unless every caller closes it.
        """
        if self.BASE_URL not in LiteLLMProxySettings._sync_clients:
            LiteLLMProxySettings._sync_clients[self.BASE_URL] = httpx.Client(
                headers=self.authorization_header,
                base_url=self.BASE_URL,
            )
        return LiteLLMProxySettings._sync_clients[self.BASE_URL]

    @property
    def httpx_aclient(self) -> httpx.AsyncClient:
        """Shared, and callers must not close it — see `httpx_client`."""
        return LiteLLMProxySettings.pooled_async_client(
            f"httpx:{self.BASE_URL}",
            lambda: httpx.AsyncClient(headers=self.authorization_header, base_url=self.BASE_URL),
        )

    @property
    def openai_aclient(self) -> openai.AsyncClient:
        """Shared, and callers must not close it — see `httpx_client`."""
        return LiteLLMProxySettings.pooled_async_client(
            f"openai:{self.BASE_URL}",
            lambda: openai.AsyncClient(api_key=self.API_KEY.get_secret_value(), base_url=self.BASE_URL),
        )
