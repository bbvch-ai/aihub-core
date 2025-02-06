from typing import Dict, List, Optional, Tuple

import tiktoken
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from llama_index.core.callbacks import CallbackManager, TokenCountingHandler
from llama_index.llms.azure_openai import AzureOpenAI
from pydantic import Field
from typing_extensions import Callable

from aihub_lib.generative_ai.resources.costs.LLMCostTracker import LLMCostTracker
from aihub_lib.generative_ai.resources.models.AzureOpenaiResourceConfig import AzureOpenaiResourceConfig
from aihub_lib.generative_ai.resources.models.llm.chat.ChatLLMConfig import ChatLLMParameter, ChatLLMConfig


class AzureOpenAIParameter(ChatLLMParameter):
    """
    Parameters for the Azure OpenAI chat model.

    ### Why AzureOpenAIParameter?
    Azure OpenAI supports additional parameters like `logprobs`, `top_logprobs`, and `logit_bias`
    that may not be relevant for other providers. Defining them here keeps the configuration modular.
    """

    logprobs: bool = Field(False, description="If True, return log probabilities of tokens.")
    top_logprobs: Optional[int] = Field(None, description="Number of top log probabilities to return.")
    logit_bias: Optional[Dict[str, float]] = Field(None, description="Adjust probabilities of specific tokens.")


class AzureOpenAILLMConfig(ChatLLMConfig, AzureOpenaiResourceConfig):
    """
    Configuration for an Azure OpenAI chat-based LLM.

    ### Why AzureOpenAILLMConfig?
    Azure OpenAI endpoints differ from standard OpenAI usage, requiring different auth flows and parameters.
    This config handles Azure AD tokens, API versions, and cost tracking specific to Azure.

    By providing `prompt_tokens_costs_per_thousand` and `completion_tokens_costs_per_thousand`,
    we ensure cost calculations align with Azure's pricing model.
    """

    prompt_tokens_costs_per_thousand: float = Field(..., description="Cost per thousand prompt tokens.")
    completion_tokens_costs_per_thousand: float = Field(..., description="Cost per thousand completion tokens.")

    default_parameter: AzureOpenAIParameter = Field(
        ..., description="Default parameters for Azure OpenAI LLM.", default_factory=lambda: AzureOpenAIParameter()
    )

    @property
    def tokenizer(self) -> Callable[[str], List[int]]:
        return tiktoken.encoding_for_model(self.name).encode

    def to_llama_index(
        self, model_parameter: Optional[AzureOpenAIParameter] = None
    ) -> Tuple[AzureOpenAI, LLMCostTracker]:
        """
        Instantiate an AzureOpenAI LLM and a LLMCostTracker.

        Uses Azure AD credentials and merges parameters from `default_parameter` and `model_parameter`.
        """
        token_counter = TokenCountingHandler(tokenizer=self.tokenizer)

        cost_tracker = LLMCostTracker(
            token_counter,
            prompt_tokens_costs_per_thousand=self.prompt_tokens_costs_per_thousand,
            completion_tokens_costs_per_thousand=self.completion_tokens_costs_per_thousand,
        )

        token_provider = get_bearer_token_provider(
            DefaultAzureCredential(),
            "https://cognitiveservices.azure.com/.default",
        )

        additional_kwargs = self.merge_model_params(model_parameter)

        azure_open_ai = AzureOpenAI(
            model=self.name,
            azure_endpoint=self.base_url,
            use_azure_ad=True,
            azure_ad_token_provider=token_provider,
            api_version=self.api_version,
            temperature=additional_kwargs.pop("temperature"),
            additional_kwargs=additional_kwargs,
            callback_manager=CallbackManager([token_counter]),
            engine=self.name,
        )

        return azure_open_ai, cost_tracker
