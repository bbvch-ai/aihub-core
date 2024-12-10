from typing import Optional, Tuple

import tiktoken
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from llama_index.core.callbacks import CallbackManager, TokenCountingHandler
from llama_index.embeddings.azure_openai import AzureOpenAIEmbedding

from lib_core.generative_ai.llms.costs.LLMCostTracker import LLMCostTracker
from lib_core.generative_ai.llms.models.embedding.EmbeddingLLMConfig import EmbeddingLLMConfig, \
    EmbeddingLLMModelParameter


class AzureOpenAIEmbeddingParameter(EmbeddingLLMModelParameter):
    dimensions: Optional[int] = None
    encoding_format: str = "float"


class AzureOpenAIEmbeddingConfig(EmbeddingLLMConfig):
    embedding_tokens_costs_per_thousand: float = 0.0
    api_endpoint: str
    api_version: str

    default_parameter: AzureOpenAIEmbeddingParameter

    def to_llama_index(
        self, model_parameter: Optional[AzureOpenAIEmbeddingParameter] = None
    ) -> Tuple[AzureOpenAIEmbedding, LLMCostTracker]:
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
