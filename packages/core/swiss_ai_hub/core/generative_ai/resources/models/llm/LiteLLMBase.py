import abc
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from functools import lru_cache
from typing import TYPE_CHECKING, Annotated, Any

from llama_index.core.utils import Tokenizer
from pydantic import Field

from swiss_ai_hub.core.generative_ai.resources.costs.LLMCostTracker import LLMCostTracker
from swiss_ai_hub.core.infrastructure.litellm.LiteLLMProxySettings import LiteLLMProxySettings
from swiss_ai_hub.core.nats.events.form.elements.ModelSelect import ModelSelect
from swiss_ai_hub.core.nats.events.form.elements.Select import Select
from swiss_ai_hub.core.nats.events.form.Form import Form

if TYPE_CHECKING:
    from swiss_ai_hub.core.displayers.EventDisplayer import EventDisplayer


@lru_cache(maxsize=1)
def _fetch_all_model_info_cached() -> dict[str, Any]:
    client = LiteLLMProxySettings().httpx_client
    return client.get("/v1/model/info").json()


class LiteLLMBase[OpenAILike](Form, abc.ABC):
    """
    Base class for LiteLLM model configurations.

    Supports duality pattern: model_name can be either a string (data mode)
    or a Select element (form mode) for model selection.
    """

    model_name: Annotated[str | Select | ModelSelect, Field(description="Name of the model.")]

    @property
    def token_counter(self) -> Callable[[str], list[int]]:
        client = LiteLLMProxySettings().httpx_client

        def token_counter(content: str) -> list[int]:
            token_response = client.post(
                "/utils/token_counter", json={"model": self.model_name, "prompt": content}
            ).json()
            return [0] * token_response["total_tokens"]

        return token_counter

    @property
    def tokenizer(self) -> type[Tokenizer]:
        token_counter = self.token_counter

        class Tokenizer:
            def encode(self, text: str, *args: Any, **kwargs: Any) -> list[Any]:
                return token_counter(text)

        return Tokenizer

    @abc.abstractmethod
    def to_llama_index(self) -> tuple[OpenAILike, LLMCostTracker]:
        pass

    @asynccontextmanager
    async def cost_reporting_llm(
        self,
        displayer: "EventDisplayer",
    ) -> AsyncIterator[OpenAILike]:
        """
        Async context manager that yields an LLM configured with merged parameters and a system prompt.
        After the block, it reports costs to `displayer`.
        """
        llm, cost_tracker = self.to_llama_index()
        yield llm
        await displayer.display_llm_costs(self.model_name, cost_tracker)

    def get_model_info(self) -> dict[str, Any]:
        model_info = _fetch_all_model_info_cached()

        models = model_info["data"]
        model_info = next((model for model in models if model["model_name"] == self.model_name), None)
        if not model_info:
            raise ValueError(f"Model {self.model_name} not found in LiteLLM Proxy.")

        return model_info
