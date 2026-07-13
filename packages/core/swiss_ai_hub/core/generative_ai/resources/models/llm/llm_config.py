from typing import Annotated, Self

from llama_index.core.callbacks import CallbackManager, TokenCountingHandler
from llama_index.llms.openai_like import OpenAILike
from opentelemetry.propagate import inject
from pydantic import Field

from swiss_ai_hub.core.form.constraints import Ge, Le
from swiss_ai_hub.core.form.elements.checkbox import Checkbox
from swiss_ai_hub.core.form.elements.input_number import InputNumber
from swiss_ai_hub.core.form.elements.model_select import ModelSelect
from swiss_ai_hub.core.form.form import Form
from swiss_ai_hub.core.generative_ai.resources.costs.llm_cost_tracker import LLMCostTracker
from swiss_ai_hub.core.generative_ai.resources.models.llm.lite_llm_base import LiteLLMBase
from swiss_ai_hub.core.generative_ai.resources.models.llm.resilient_open_ai_like import ResilientOpenAILike
from swiss_ai_hub.core.i18n.locale_string import LocaleString
from swiss_ai_hub.core.infrastructure.litellm.lite_llm_proxy_settings import LiteLLMProxySettings


class LLMParameter(Form):
    """
    Parameters for a chat-based LLM.

    Chat-oriented models might need parameters controlling randomness, token limits, or repetition.
    By defining them here, we standardize parameter handling and ensure easy customization.

    Supports duality pattern: instantiate with InputNumber/Checkbox for form mode,
    or with primitive values for data mode.
    """

    temperature: Annotated[
        float | InputNumber,
        Field(default=0.0, description="The temperature to use during generation."),
        Ge(0.0),
        Le(2.0),
    ] = 0.0
    logprobs: Annotated[
        bool | None | Checkbox,
        Field(
            description="Whether to return logprobs per token.",
            default=None,
        ),
    ] = None
    top_logprobs: Annotated[
        int | InputNumber,
        Field(default=0, description="The number of top token log probs to return."),
        Ge(0),
        Le(20),
    ] = 0
    timeout: Annotated[
        float | InputNumber,
        Field(default=600.0, description="The timeout, in seconds, for API requests."),
        Ge(0),
    ] = 600.0

    @classmethod
    def as_form(cls) -> Self:
        """Factory method to create a form-mode LLMParameter with input elements."""
        return cls(
            temperature=InputNumber(
                label=LocaleString.from_i18n_path("lib.llm.config.temperature.label"),
                help=LocaleString.from_i18n_path("lib.llm.config.temperature.help"),
                min=0.0,
                max=2.0,
                step=0.1,
                value=0.0,
                min_fraction_digits=0,
                max_fraction_digits=1,
            ),
            logprobs=Checkbox(
                label=LocaleString.from_i18n_path("lib.llm.config.logprobs.label"),
                help=LocaleString.from_i18n_path("lib.llm.config.logprobs.help"),
                ref="llm_logprobs_enabled",
            ),
            top_logprobs=InputNumber(
                label=LocaleString.from_i18n_path("lib.llm.config.top_logprobs.label"),
                help=LocaleString.from_i18n_path("lib.llm.config.top_logprobs.help"),
                min=0,
                max=20,
                step=1,
                condition_if="$get(llm_logprobs_enabled).value",
            ),
            timeout=InputNumber(
                label=LocaleString.from_i18n_path("lib.llm.config.timeout.label"),
                help=LocaleString.from_i18n_path("lib.llm.config.timeout.help"),
                min=0,
                step=10,
            ),
        )


class LLMConfig(LiteLLMBase[OpenAILike]):
    """
    Configuration for a chat-based LLM, providing default parameters and a method
    to instantiate a chat LLM and cost tracker for llama_index.

    ### Why LLMConfig?
    Chat models (like OpenAI's ChatGPT variants) often require parameters like temperature or max_tokens.
    With LLMConfig, we integrate these parameters and the cost tracking mechanism in one place.

    Supports duality pattern for form rendering and data validation.
    """

    default_parameter: Annotated[
        LLMParameter,
        Field(description="Default parameters for the chat-based LLM."),
    ] = LLMParameter()

    @classmethod
    def as_form(cls) -> Self:
        """Factory method to create a form-mode LLMConfig."""
        return cls(
            model_name=ModelSelect(
                label=LocaleString.from_i18n_path("lib.llm.config.model.label"),
                help=LocaleString.from_i18n_path("lib.llm.config.model.help"),
                mode="chat",
            ),
            default_parameter=LLMParameter.as_form(),
        )

    def to_llama_index(self, extra_headers: dict[str, str] | None = None) -> tuple[OpenAILike, LLMCostTracker]:
        """
        Instantiate an OpenAILike model with local endpoint logic and a LLMCostTracker.

        This uses the OpenAILike wrapper since it mimics OpenAI-like APIs. The tokenizer is retrieved
        from the local model, and parameters are merged to configure the model's behavior.
        """
        config = LiteLLMProxySettings()
        model_info = self.get_model_info()

        context_size = model_info["model_info"]["max_input_tokens"]
        is_chat_model = model_info["model_info"]["mode"] == "chat"
        is_function_calling_model = model_info["model_info"]["supports_function_calling"]
        max_tokens = model_info["model_info"]["max_output_tokens"]
        supports_response_schema = model_info["model_info"].get("supports_response_schema") or False

        token_counter = TokenCountingHandler(tokenizer=self.token_counter)
        cost_tracker = LLMCostTracker(
            token_counter=token_counter,
            prompt_tokens_costs_per_thousand=model_info["model_info"]["input_cost_per_token"] * 1000,
            completion_tokens_costs_per_thousand=model_info["model_info"]["output_cost_per_token"] * 1000,
        )

        default_headers = {}
        inject(default_headers)
        if extra_headers:
            default_headers.update(extra_headers)

        open_ai_like = ResilientOpenAILike(
            model=self.model_name,
            api_base=config.BASE_URL,
            api_key=config.API_KEY.get_secret_value(),
            temperature=self.default_parameter.temperature,
            context_window=context_size,
            is_chat_model=is_chat_model,
            is_function_calling_model=is_function_calling_model,
            should_use_structured_outputs=supports_response_schema,
            tokenizer=self.tokenizer,
            max_tokens=max_tokens,
            logprobs=self.default_parameter.logprobs,
            top_logprobs=self.default_parameter.top_logprobs,
            callback_manager=CallbackManager([token_counter]),
            timeout=self.default_parameter.timeout,
            default_headers=default_headers,
        )

        return open_ai_like, cost_tracker
