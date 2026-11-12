import abc
from collections.abc import Callable
from functools import lru_cache
from typing import Annotated, Any

import httpx
from llama_index.core.utils import get_tokenizer
from pydantic import Field
from tenacity import Retrying, retry_if_exception, retry_if_exception_type, stop_after_attempt, wait_exponential

from swiss_ai_hub.core.form.elements.model_select import ModelSelect
from swiss_ai_hub.core.form.elements.select import Select
from swiss_ai_hub.core.form.form import Form
from swiss_ai_hub.core.generative_ai.resources.costs.llm_cost_tracker import LLMCostTracker
from swiss_ai_hub.core.generative_ai.resources.tokenizers.model_token_budget import ModelTokenBudget
from swiss_ai_hub.core.infrastructure.litellm.lite_llm_proxy_settings import LiteLLMProxySettings

# A burst of MinerU VLM calls can keep LiteLLM's single worker from answering for minutes; with httpx's 5 s
# default every pipeline run that started meanwhile failed on this one read-only call.
MODEL_INFO_TIMEOUT = httpx.Timeout(30.0, connect=5.0)
MODEL_INFO_ATTEMPTS = 5


@lru_cache(maxsize=1)
def _fetch_all_model_info_cached() -> dict[str, Any]:
    """Retries only what can heal on its own (network failures, 5xx); a 4xx such as a bad key fails at once."""
    for attempt in Retrying(
        retry=retry_if_exception_type(httpx.TransportError)
        | retry_if_exception(
            lambda error: isinstance(error, httpx.HTTPStatusError) and error.response.status_code >= 500
        ),
        stop=stop_after_attempt(MODEL_INFO_ATTEMPTS),
        wait=wait_exponential(multiplier=2, max=30),
        reraise=True,
    ):
        with attempt:
            response = LiteLLMProxySettings().httpx_client.get("/v1/model/info", timeout=MODEL_INFO_TIMEOUT)
            response.raise_for_status()
            return response.json()
    raise RuntimeError("Retry loop exited unexpectedly")


class LiteLLMBase[OpenAILike](Form, abc.ABC):
    """
    Base class for LiteLLM model configurations.

    Supports duality pattern: model_name can be either a string (data mode)
    or a Select element (form mode) for model selection.
    """

    model_name: Annotated[str | Select | ModelSelect, Field(description="Name of the model.")]

    @property
    def token_counter(self) -> Callable[[str], list[int]]:
        return get_tokenizer()

    @abc.abstractmethod
    def to_llama_index(
        self, extra_headers: dict[str, str] | None = None, api_key: str | None = None
    ) -> tuple[OpenAILike, LLMCostTracker]:
        pass

    def get_model_info(self) -> dict[str, Any]:
        model_info = _fetch_all_model_info_cached()

        models = model_info["data"]
        model_info = next((model for model in models if model["model_name"] == self.model_name), None)
        if not model_info:
            raise ValueError(f"Model {self.model_name} not found in LiteLLM Proxy.")

        return model_info

    def token_budget(
        self, max_input_tokens: Annotated[int | None, "An explicit window, winning over the declared one"] = None
    ) -> ModelTokenBudget:
        """Blocking on the first call per process (the model info is fetched once): async callers run it in a thread."""
        return ModelTokenBudget.for_model(self.model_name, self.get_model_info()["model_info"], max_input_tokens)
