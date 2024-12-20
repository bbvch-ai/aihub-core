from typing import Optional, Tuple

import tiktoken
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from llama_index.core.callbacks import CallbackManager, TokenCountingHandler
from llama_index.embeddings.azure_openai import AzureOpenAIEmbedding
from pydantic import Field

from lib_core.generative_ai.llms.costs.LLMCostTracker import LLMCostTracker
from lib_core.generative_ai.llms.models.embedding.EmbeddingLLMConfig import EmbeddingLLMConfig, EmbeddingLLMModelParameter


class AzureOpenAIEmbeddingParameter(EmbeddingLLMModelParameter):
    """
    Parameters for Azure OpenAI embeddings.

    ### Why AzureOpenAIEmbeddingParameter?
    Although embedding models may have fewer parameters, keeping a separate parameter class
    maintains consistency and allows easy extension if needed.
    """

    dimensions: Optional[int] = Field(None, description="Number of embedding dimensions if applicable.")
    encoding_format: str = Field("float", description="The encoding format of the returned embeddings.")


class AzureOpenAIEmbeddingConfig(EmbeddingLLMConfig):
    """
    Configuration for an Azure OpenAI embedding model.

    ### Why AzureOpenAIEmbeddingConfig?
    Azure embedding models differ from chat models in usage and cost structure.
    This config sets embedding costs and configures Azure AD authentication, ensuring that
    embedding operations integrate seamlessly with llama_index and cost tracking.
    """

    embedding_tokens_costs_per_thousand: float = Field(0.0, description="Cost per thousand embedding tokens.")
    api_endpoint: str = Field(..., description="Azure OpenAI API endpoint for embeddings.")
    api_version: str = Field(..., description="Azure OpenAI API version for embeddings.")

    default_parameter: AzureOpenAIEmbeddingParameter = Field(..., description="Default parameters for Azure OpenAI embeddings.")

    def to_llama_index(
        self, model_parameter: Optional[AzureOpenAIEmbeddingParameter] = None
    ) -> Tuple[AzureOpenAIEmbedding, LLMCostTracker]:
        """
        Instantiate an AzureOpenAIEmbedding and a LLMCostTracker for embedding operations.

        Uses Azure AD credentials and merges parameters from `default_parameter` and `model_parameter`.
        """
        tokenizer = tiktoken.encoding_for_model(self.name).encode
        token_counter = TokenCountingHandler(tokenizer=tokenizer)

        cost_tracker = LLMCostTracker(
            token_counter,
            embedding_tokens_costs_per_thousand=self.embedding_tokens_costs_per_thousand,
        )

        token_provider = get_bearer_token_provider(
            DefaultAzureCredential(),
            "https://cognitiveservices.azure.com/.default",
        )

        additional_kwargs = self.merge_model_params(model_parameter)

        azure_open_ai_embedding = AzureOpenAIEmbedding(
            model=self.name,
            azure_endpoint=self.api_endpoint,
            azure_ad_token_provider=token_provider,
            api_version=self.api_version,
            additional_kwargs=additional_kwargs,
            callback_manager=CallbackManager([token_counter]),
        )

        return azure_open_ai_embedding, cost_tracker
