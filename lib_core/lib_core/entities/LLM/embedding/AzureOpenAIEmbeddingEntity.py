from typing import Optional, Tuple

import tiktoken
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from llama_index.core.callbacks import CallbackManager, TokenCountingHandler
from llama_index.embeddings.azure_openai import AzureOpenAIEmbedding
from mongoengine import EmbeddedDocumentField, FloatField, IntField, StringField

from lib_core.handlers.CostTracker import CostTracker
from lib_core.entities.LLM.embedding.EmbeddingLLMEntity import EmbeddingLLMEntity, EmbeddingLLMModelParameter


class AzureOpenAIEmbeddingParameter(EmbeddingLLMModelParameter):
    dimensions = IntField(required=False)
    encoding_format = StringField(required=False, default="float")


class AzureOpenAIEmbeddingEntity(EmbeddingLLMEntity):
    embedding_tokens_costs_per_thousand = FloatField(required=False, default=0)
    api_endpoint = StringField(required=True)
    api_version = StringField(required=True)

    default_parameter = EmbeddedDocumentField(AzureOpenAIEmbeddingParameter, required=True)

    def to_llama_index(
        self, model_parameter: Optional[AzureOpenAIEmbeddingParameter] = None
    ) -> Tuple[AzureOpenAIEmbedding, CostTracker]:
        tokenizer = tiktoken.encoding_for_model(self.name).encode
        token_counter = TokenCountingHandler(tokenizer=tokenizer)

        cost_tracker = CostTracker(
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
