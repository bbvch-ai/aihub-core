import abc
from collections.abc import Callable
from functools import lru_cache
from typing import Annotated, Any

from llama_index.core.utils import get_tokenizer
from pydantic import Field

from swiss_ai_hub.core.form.elements.model_select import ModelSelect
from swiss_ai_hub.core.form.elements.select import Select
from swiss_ai_hub.core.form.form import Form
from swiss_ai_hub.core.generative_ai.resources.costs.llm_cost_tracker import LLMCostTracker
from swiss_ai_hub.core.infrastructure.litellm.lite_llm_proxy_settings import LiteLLMProxySettings


@lru_cache(maxsize=1)
def _fetch_all_model_info_cached() -> dict[str, Any]:
    return LiteLLMProxySettings().httpx_client.get("/v1/model/info").json()


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
