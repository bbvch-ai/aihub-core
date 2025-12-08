from typing import Annotated

from llama_index.core.callbacks import CallbackManager, TokenCountingHandler
from llama_index.llms.openai_like import OpenAILike
from opentelemetry.propagate import inject
from pydantic import BaseModel, Field

from aihub_lib.generative_ai.resources.costs.LLMCostTracker import LLMCostTracker
from aihub_lib.generative_ai.resources.models.llm.LiteLLMBase import LiteLLMBase
from aihub_lib.infrastructure.litellm.LiteLLMProxySettings import LiteLLMProxySettings


class LLMParameter(BaseModel):
    """
    Parameters for a chat-based LLM.

    Chat-oriented models might need parameters controlling randomness, token limits, or repetition.
    By defining them here, we standardize parameter handling and ensure easy customization.
    """

    temperature: float = Field(
        default=0.0,
        description="The temperature to use during generation.",
        ge=0.0,
        le=2.0,
    )
    logprobs: bool | None = Field(
        description="Whether to return logprobs per token.",
        default=None,
    )
    top_logprobs: int = Field(
        description="The number of top token log probs to return.",
        default=0,
        ge=0,
        le=20,
    )
    timeout: float = Field(
        default=600.0,
        description="The timeout, in seconds, for API requests.",
        ge=0,
    )


class LLMConfig(LiteLLMBase[OpenAILike]):
    """
    Configuration for a chat-based LLM, providing default parameters and a method
    to instantiate a chat LLM and cost tracker for llama_index.

    ### Why LLMConfig?
    Chat models (like OpenAI's ChatGPT variants) often require parameters like temperature or max_tokens.
    With LLMConfig, we integrate these parameters and the cost tracking mechanism in one place.
    """

    model_name: Annotated[str, Field(description="Name of the chat-based LLM model.")]
    default_parameter: Annotated[LLMParameter, Field(description="Default parameters for the chat-based LLM.")] = (
        LLMParameter()
    )

    def to_llama_index(self) -> tuple[OpenAILike, LLMCostTracker]:
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

        token_counter = TokenCountingHandler(tokenizer=self.token_counter)
        cost_tracker = LLMCostTracker(
            token_counter=token_counter,
            prompt_tokens_costs_per_thousand=model_info["model_info"]["input_cost_per_token"] * 1000,
            completion_tokens_costs_per_thousand=model_info["model_info"]["output_cost_per_token"] * 1000,
        )

        default_headers = {}
        inject(default_headers)

        open_ai_like = OpenAILike(
            model=self.model_name,
            api_base=config.BASE_URL,
            api_key=config.API_KEY.get_secret_value(),
            temperature=self.default_parameter.temperature,
            context_window=context_size,
            is_chat_model=is_chat_model,
            is_function_calling_model=is_function_calling_model,
            tokenizer=self.tokenizer,
            max_tokens=max_tokens,
            logprobs=self.default_parameter.logprobs,
            top_logprobs=self.default_parameter.top_logprobs,
            callback_manager=CallbackManager([token_counter]),
            timeout=self.default_parameter.timeout,
            default_headers=default_headers,
        )

        return open_ai_like, cost_tracker
