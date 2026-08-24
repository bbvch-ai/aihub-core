import abc
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from functools import lru_cache
from typing import TYPE_CHECKING, Annotated, Any

from llama_index.core.utils import get_tokenizer
from pydantic import Field

from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.form.elements.model_select import ModelSelect
from swiss_ai_hub.core.form.elements.select import Select
from swiss_ai_hub.core.form.form import Form
from swiss_ai_hub.core.generative_ai.resources.costs.llm_cost_tracker import LLMCostTracker
from swiss_ai_hub.core.infrastructure.litellm.lite_llm_proxy_settings import LiteLLMProxySettings
from swiss_ai_hub.core.infrastructure.litellm.lite_llm_service import LiteLLMService

if TYPE_CHECKING:
    from swiss_ai_hub.core.displayers.event_displayer import EventDisplayer


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

    @asynccontextmanager
    async def cost_reporting_llm(
        self,
        displayer: "EventDisplayer",
        extra_headers: dict[str, str] | None = None,
        user: UserIdentity | None = None,
    ) -> AsyncIterator[OpenAILike]:
        """
        Async context manager that yields an LLM configured with merged parameters and a system prompt.
        After the block, it reports costs to `displayer`.
        """
        # The per-user key is the only carrier that reaches LiteLLM: it sets `user` on every spend log row
        # and activates USER_MAX_BUDGET. Tenant is NOT sent — custom request tags (`x-litellm-tags` and
        # `metadata.tags`) are an enterprise feature and this deployment silently drops them, verified with
        # a 200 response and no tag in /spend/logs. Tenant attribution lives on LLMCostEvent instead; see
        # #786 before adding a gateway-side carrier (LiteLLM teams put tenant on `team_id` natively).
        api_key = await LiteLLMService.api_key_for_user(user) if user else None

        llm, cost_tracker = self.to_llama_index(extra_headers=extra_headers, api_key=api_key)
        yield llm
        await displayer.display_llm_costs(self.model_name, cost_tracker, user)

    def get_model_info(self) -> dict[str, Any]:
        model_info = _fetch_all_model_info_cached()

        models = model_info["data"]
        model_info = next((model for model in models if model["model_name"] == self.model_name), None)
        if not model_info:
            raise ValueError(f"Model {self.model_name} not found in LiteLLM Proxy.")

        return model_info
