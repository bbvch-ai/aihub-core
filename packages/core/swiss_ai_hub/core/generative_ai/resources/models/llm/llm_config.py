from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Annotated, Any, Self

from llama_index.core.callbacks import CallbackManager, TokenCountingHandler
from opentelemetry.propagate import inject
from pydantic import Field

from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.form.constraints import Ge, Le
from swiss_ai_hub.core.form.elements.checkbox import Checkbox
from swiss_ai_hub.core.form.elements.input_number import InputNumber
from swiss_ai_hub.core.form.elements.model_bound_input_number import ModelBoundInputNumber
from swiss_ai_hub.core.form.elements.model_gated_checkbox import ModelGatedCheckbox
from swiss_ai_hub.core.form.elements.model_select import ModelSelect
from swiss_ai_hub.core.form.form import Form
from swiss_ai_hub.core.generative_ai.resources.costs.llm_cost_tracker import LLMCostTracker
from swiss_ai_hub.core.generative_ai.resources.models.llm.lite_llm_base import LiteLLMBase
from swiss_ai_hub.core.generative_ai.resources.models.llm.resilient_open_ai_like import ResilientOpenAILike
from swiss_ai_hub.core.i18n.locale_string import LocaleString
from swiss_ai_hub.core.infrastructure.litellm.lite_llm_proxy_settings import LiteLLMProxySettings
from swiss_ai_hub.core.infrastructure.litellm.lite_llm_service import LiteLLMService

if TYPE_CHECKING:
    from swiss_ai_hub.core.displayers.event_displayer import EventDisplayer

# What a model without a curated `default_temperature` is sampled at; the value every model used before
# defaults became per model.
DEFAULT_TEMPERATURE = 0.0


class LLMParameter(Form):
    """
    Parameters for a chat-based LLM.

    Chat-oriented models might need parameters controlling randomness, token limits, or repetition.
    By defining them here, we standardize parameter handling and ensure easy customization.

    Supports duality pattern: instantiate with InputNumber/Checkbox for form mode,
    or with primitive values for data mode.
    """

    temperature: Annotated[
        float | None | InputNumber,
        Field(
            default=None,
            description="The temperature to use during generation. None uses the model's curated default.",
        ),
        Ge(0.0),
        Le(2.0),
    ] = None
    top_p: Annotated[
        float | None | InputNumber,
        Field(
            default=None,
            description="The nucleus-sampling probability mass. None uses the model's curated default.",
        ),
        Ge(0.0),
        Le(1.0),
    ] = None
    accept_images: Annotated[
        bool | Checkbox,
        Field(description="Whether images in the conversation are passed to the model."),
    ] = True
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
        Field(default=300.0, description="The timeout, in seconds, for API requests."),
        Ge(0),
    ] = 300.0

    @classmethod
    def as_form(cls) -> Self:
        """Factory method to create a form-mode LLMParameter with input elements."""
        return cls(
            temperature=ModelBoundInputNumber(
                label=LocaleString.from_i18n_path("lib.llm.config.temperature.label"),
                help=LocaleString.from_i18n_path("lib.llm.config.temperature.help"),
                override_label=LocaleString.from_i18n_path("lib.llm.config.temperature.toggle_label"),
                model_ref="../model_name",
                default_from="default_temperature",
                fallback_default=DEFAULT_TEMPERATURE,
                min=0.0,
                max=2.0,
                step=0.1,
                min_fraction_digits=1,
                max_fraction_digits=2,
            ),
            top_p=ModelBoundInputNumber(
                label=LocaleString.from_i18n_path("lib.llm.config.top_p.label"),
                help=LocaleString.from_i18n_path("lib.llm.config.top_p.help"),
                override_label=LocaleString.from_i18n_path("lib.llm.config.top_p.toggle_label"),
                model_ref="../model_name",
                default_from="default_top_p",
                min=0.0,
                max=1.0,
                step=0.05,
                min_fraction_digits=1,
                max_fraction_digits=2,
            ),
            accept_images=ModelGatedCheckbox(
                label=LocaleString.from_i18n_path("lib.llm.config.accept_images.label"),
                help=LocaleString.from_i18n_path("lib.llm.config.accept_images.help"),
                model_ref="../model_name",
                requires="supports_vision",
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


class LLMConfig(LiteLLMBase[ResilientOpenAILike]):
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
    def as_form(cls, include_default_parameter: bool = True) -> Self:
        """
        Factory method to create a form-mode LLMConfig.

        Pass `include_default_parameter=False` to render the model picker alone, for configs whose
        generation parameters are derived from another LLMConfig rather than chosen by the user.
        """
        return cls(
            model_name=ModelSelect(
                label=LocaleString.from_i18n_path("lib.llm.config.model.label"),
                help=LocaleString.from_i18n_path("lib.llm.config.model.help"),
                mode="chat",
            ),
            default_parameter=LLMParameter.as_form() if include_default_parameter else LLMParameter(),
        )

    @classmethod
    def deterministic(cls, model_name: str) -> Self:
        """A config pinned to `DEFAULT_TEMPERATURE`, for platform-internal calls (ingestion, translation, drafting)
        that must not pick up a model's sampling default, which is tuned for chat rather than reproducibility."""
        return cls(model_name=model_name, default_parameter=LLMParameter(temperature=DEFAULT_TEMPERATURE))

    def as_task_llm(self, model_name: str) -> Self:
        """
        A task variant of this config for auxiliary/classification steps.

        Those steps reuse the main model's generation parameters and never need log probabilities,
        so only the model itself is configurable. An unset temperature is pinned to `DEFAULT_TEMPERATURE` rather
        than left to the model's default: these steps classify and condense, which needs reproducible output, while
        a model's default is tuned for chat.
        """
        temperature = self.default_parameter.temperature
        return self.model_copy(
            deep=True,
            update={
                "model_name": model_name,
                "default_parameter": LLMParameter(
                    temperature=DEFAULT_TEMPERATURE if temperature is None else temperature,
                    top_p=self.default_parameter.top_p,
                    accept_images=self.default_parameter.accept_images,
                    timeout=self.default_parameter.timeout,
                    logprobs=False,
                ),
            },
        )

    @asynccontextmanager
    async def cost_reporting_llm(
        self,
        displayer: "EventDisplayer",
        extra_headers: dict[str, str] | None = None,
        user: UserIdentity | None = None,
    ) -> AsyncIterator[ResilientOpenAILike]:
        """
        Async context manager that yields an LLM configured with merged parameters and a system prompt.

        On exit, also when the block raised, it reports the costs to `displayer` — tokens spent before a failure
        are spent all the same — and closes the LLM's clients (see `ResilientOpenAILike.aclose`).
        """
        # The per-user key is the only carrier that reaches LiteLLM: it sets `user` on every spend log row
        # and activates USER_MAX_BUDGET. Tenant is NOT sent — custom request tags (`x-litellm-tags` and
        # `metadata.tags`) are an enterprise feature and this deployment silently drops them, verified with
        # a 200 response and no tag in /spend/logs. Tenant attribution lives on LLMCostEvent instead; see
        # #786 before adding a gateway-side carrier (LiteLLM teams put tenant on `team_id` natively).
        api_key = await LiteLLMService.api_key_for_user(user) if user else None

        llm, cost_tracker = self.to_llama_index(extra_headers=extra_headers, api_key=api_key)
        try:
            yield llm
        finally:
            try:
                await displayer.display_llm_costs(self.model_name, cost_tracker, user)
            finally:
                await llm.aclose()

    @property
    def max_input_tokens(self) -> int | None:
        """The model's context window as LiteLLM declares it, or None when it declares none.

        Callers that bound a prompt need this number before building one, not after the provider rejects it.
        `None` rather than a raise: a guard must not turn a model with an incomplete LiteLLM entry into a
        failing run. `to_llama_index` keeps its own strict lookup, where a missing window is a real defect.
        """
        return self.get_model_info()["model_info"].get("max_input_tokens")

    @property
    def supports_vision(self) -> bool | None:
        """Whether the model reads images, or None when LiteLLM leaves the flag unset, as it does for most models."""
        return self.get_model_info()["model_info"].get("supports_vision")

    @property
    def max_images(self) -> int | None:
        """The most images one prompt may carry, as curated in the LiteLLM config, or None when it sets no limit."""
        return self.get_model_info()["model_info"].get("max_images")

    def resolved_temperature(self, model_info: dict[str, Any]) -> float:
        """The configured temperature, else the model's curated default, else `DEFAULT_TEMPERATURE`."""
        if self.default_parameter.temperature is not None:
            return self.default_parameter.temperature
        return model_info.get("default_temperature", DEFAULT_TEMPERATURE)

    def resolved_top_p(self, model_info: dict[str, Any]) -> float | None:
        """The configured top_p, else the model's curated default; None leaves it to the provider."""
        if self.default_parameter.top_p is not None:
            return self.default_parameter.top_p
        return model_info.get("default_top_p")

    def to_llama_index(
        self, extra_headers: dict[str, str] | None = None, api_key: str | None = None
    ) -> tuple[ResilientOpenAILike, LLMCostTracker]:
        """
        Instantiate an OpenAILike model with local endpoint logic and a LLMCostTracker.

        Streamed calls ask the gateway to report real token usage on the final chunk, so
        ``TokenCountingHandler`` doesn't fall back to re-tokenizing the whole chat history locally on
        every call. That request lives in ``ResilientOpenAILike`` rather than in ``additional_kwargs``
        here, because endpoints that reject ``stream_options`` need a plain-stream retry.
        """
        config = LiteLLMProxySettings()
        model_info = self.get_model_info()

        context_size = model_info["model_info"]["max_input_tokens"]
        is_chat_model = model_info["model_info"]["mode"] == "chat"
        is_function_calling_model = model_info["model_info"]["supports_function_calling"]
        max_tokens = model_info["model_info"]["max_output_tokens"]
        supports_response_schema = model_info["model_info"].get("supports_response_schema") or False
        top_p = self.resolved_top_p(model_info["model_info"])

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
            api_key=api_key or config.API_KEY.get_secret_value(),
            temperature=self.resolved_temperature(model_info["model_info"]),
            additional_kwargs={"top_p": top_p} if top_p is not None else {},
            context_window=context_size,
            is_chat_model=is_chat_model,
            is_function_calling_model=is_function_calling_model,
            should_use_structured_outputs=supports_response_schema,
            max_tokens=max_tokens,
            logprobs=self.default_parameter.logprobs,
            top_logprobs=self.default_parameter.top_logprobs,
            callback_manager=CallbackManager([token_counter]),
            timeout=self.default_parameter.timeout,
            connect_timeout=config.CONNECT_TIMEOUT_SECONDS,
            default_headers=default_headers,
        )

        return open_ai_like, cost_tracker
