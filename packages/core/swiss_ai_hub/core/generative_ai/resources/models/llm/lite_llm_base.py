import abc
from collections.abc import Callable
from typing import Annotated, Any

from llama_index.core.utils import get_tokenizer
from pydantic import Field

from swiss_ai_hub.core.form.elements.model_select import ModelSelect
from swiss_ai_hub.core.form.elements.select import Select
from swiss_ai_hub.core.form.form import Form
from swiss_ai_hub.core.generative_ai.resources.costs.llm_cost_tracker import LLMCostTracker
from swiss_ai_hub.core.generative_ai.resources.models.llm.lite_llm_model_info import LiteLLMModelInfo
from swiss_ai_hub.core.generative_ai.resources.tokenizers.model_token_budget import ModelTokenBudget


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
        model_info = LiteLLMModelInfo.all_models()

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
