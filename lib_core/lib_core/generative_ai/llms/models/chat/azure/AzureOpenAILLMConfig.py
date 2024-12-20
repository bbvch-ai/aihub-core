from typing import Optional, Tuple, Dict

import tiktoken
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from llama_index.core.callbacks import CallbackManager, TokenCountingHandler
from llama_index.llms.azure_openai import AzureOpenAI
from pydantic import Field

from lib_core.generative_ai.llms.costs.LLMCostTracker import LLMCostTracker
from lib_core.generative_ai.llms.models.chat.ChatLLMConfig import ChatLLMConfig, ChatLLMModelParameter


class AzureOpenAIParameter(ChatLLMModelParameter):
    """
    Parameters for the Azure OpenAI chat model.

    ### Why AzureOpenAIParameter?
    Azure OpenAI supports additional parameters like `logprobs`, `top_logprobs`, and `logit_bias`
    that may not be relevant for other providers. Defining them here keeps the configuration modular.
    """

    logprobs: bool = Field(False, description="If True, return log probabilities of tokens.")
    top_logprobs: Optional[int] = Field(None, description="Number of top log probabilities to return.")
    logit_bias: Optional[Dict[str, float]] = Field(None, description="Adjust probabilities of specific tokens.")


class AzureOpenAILLMConfig(ChatLLMConfig):
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
    api_version: str = Field(..., description="Azure OpenAI API version.")

    default_parameter: AzureOpenAIParameter = Field(..., description="Default parameters for Azure OpenAI LLM.")

    def to_llama_index(self, model_parameter: Optional[AzureOpenAIParameter] = None) -> Tuple[AzureOpenAI, LLMCostTracker]:
        """
        Instantiate an AzureOpenAI LLM and a LLMCostTracker.

        Uses Azure AD credentials and merges parameters from `default_parameter` and `model_parameter`.
        """
        tokenizer = tiktoken.encoding_for_model(self.name).encode
        token_counter = TokenCountingHandler(tokenizer=tokenizer)

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
            azure_endpoint=self.api_endpoint,
            use_azure_ad=True,
            azure_ad_token_provider=token_provider,
            api_version=self.api_version,
            temperature=additional_kwargs.pop("temperature"),
            additional_kwargs=additional_kwargs,
            callback_manager=CallbackManager([token_counter]),
            engine=self.name,
        )

        return azure_open_ai, cost_tracker
