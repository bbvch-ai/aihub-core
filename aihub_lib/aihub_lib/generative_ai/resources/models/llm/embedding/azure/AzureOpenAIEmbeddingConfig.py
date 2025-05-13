from typing import Optional, Tuple

import tiktoken
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from llama_index.core.callbacks import CallbackManager, TokenCountingHandler
from llama_index.embeddings.azure_openai import AzureOpenAIEmbedding
from openai import NOT_GIVEN
from pydantic import Field
from typing_extensions import Annotated

from aihub_lib.generative_ai.resources.costs.LLMCostTracker import LLMCostTracker
from aihub_lib.generative_ai.resources.models.AzureOpenaiResourceConfig import AzureOpenaiResourceConfig
from aihub_lib.generative_ai.resources.models.llm.embedding.EmbeddingLLMConfig import (
    EmbeddingLLMConfig,
    EmbeddingLLMParameter,
)


class AzureOpenAIEmbeddingParameter(EmbeddingLLMParameter):
    """
    Parameters for Azure OpenAI embeddings.

    ### Why AzureOpenAIEmbeddingParameter?
    Although embedding models may have fewer parameters, keeping a separate parameter class
    maintains consistency and allows easy extension if needed.
    """

    dimensions: Annotated[
        int | NOT_GIVEN,
        Field(
            NOT_GIVEN,
            description="The number of dimensions in the embedding vector. Supported in text-embedding-3 and later models.",
        ),
    ]
    encoding_format: Annotated[str, Field(description="The encoding format of the returned embeddings.")] = "float"


class AzureOpenAIEmbeddingConfig(EmbeddingLLMConfig, AzureOpenaiResourceConfig):
    """
    Configuration for an Azure OpenAI embedding model.

    ### Why AzureOpenAIEmbeddingConfig?
    Azure embedding models differ from chat models in usage and cost structure.
    This config sets embedding costs and configures Azure AD authentication, ensuring that
    embedding operations integrate seamlessly with llama_index and cost tracking.
    """

    embedding_tokens_costs_per_thousand: Annotated[float, Field(description="Cost per thousand embedding tokens.")] = (
        0.0
    )

    default_parameter: AzureOpenAIEmbeddingParameter = Field(
        default_factory=lambda: AzureOpenAIEmbeddingParameter(),
        description="Default parameters for Azure OpenAI embeddings.",
    )

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
            azure_endpoint=self.base_url,
            azure_ad_token_provider=token_provider,
            api_version=self.api_version,
            additional_kwargs=additional_kwargs,
            callback_manager=CallbackManager([token_counter]),
        )

        return azure_open_ai_embedding, cost_tracker
