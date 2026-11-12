import logging
from threading import Lock
from typing import Any, ClassVar

import httpx
from tenacity import (
    Retrying,
    before_sleep_log,
    retry_if_exception,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from swiss_ai_hub.core.infrastructure.litellm.lite_llm_proxy_settings import LiteLLMProxySettings

logger = logging.getLogger(__name__)


class LiteLLMModelInfo:
    """The proxy's `/v1/model/info`, fetched once per process and shared by every model config.

    Callers read it synchronously, agents and the API from request paths, so a stalled proxy blocks them for as long
    as the lookup takes: by default it gives up within about 20 s. A process nobody waits on, such as a Dagster run,
    calls `wait_patiently()` so that a proxy kept busy for minutes (a MinerU burst, aihub-core-private#465) delays the
    run instead of failing it.
    """

    QUICK_ATTEMPTS: ClassVar[int] = 2
    QUICK_READ_TIMEOUT_SECONDS: ClassVar[float] = 10.0
    PATIENT_ATTEMPTS: ClassVar[int] = 6
    PATIENT_READ_TIMEOUT_SECONDS: ClassVar[float] = 30.0
    CONNECT_TIMEOUT_SECONDS: ClassVar[float] = 5.0

    _patient: ClassVar[bool] = False
    _all_models: ClassVar[dict[str, Any] | None] = None
    _fetch_lock: ClassVar[Lock] = Lock()

    @classmethod
    def wait_patiently(cls) -> None:
        """For the whole process: about 4 minutes of retries instead of about 20 s."""
        cls._patient = True

    @classmethod
    def all_models(cls) -> dict[str, Any]:
        """Threads that miss the cache together wait for one lookup instead of each retrying on their own."""
        with cls._fetch_lock:
            if cls._all_models is None:
                cls._all_models = cls._fetch()
            return cls._all_models

    @classmethod
    def _fetch(cls) -> dict[str, Any]:
        """Retries only what can heal on its own (network failures, 5xx); a 4xx such as a bad key fails at once."""
        attempts = cls.PATIENT_ATTEMPTS if cls._patient else cls.QUICK_ATTEMPTS
        read_timeout = cls.PATIENT_READ_TIMEOUT_SECONDS if cls._patient else cls.QUICK_READ_TIMEOUT_SECONDS
        for attempt in Retrying(
            retry=retry_if_exception_type(httpx.TransportError) | retry_if_exception(cls._is_server_error),
            stop=stop_after_attempt(attempts),
            wait=wait_exponential(multiplier=2, max=30),
            before_sleep=before_sleep_log(logger, logging.WARNING),
            reraise=True,
        ):
            with attempt:
                response = LiteLLMProxySettings().httpx_client.get(
                    "/v1/model/info", timeout=httpx.Timeout(read_timeout, connect=cls.CONNECT_TIMEOUT_SECONDS)
                )
                response.raise_for_status()
                return response.json()
        raise RuntimeError("Retry loop exited unexpectedly")

    @staticmethod
    def _is_server_error(error: BaseException) -> bool:
        return isinstance(error, httpx.HTTPStatusError) and error.response.status_code >= 500
