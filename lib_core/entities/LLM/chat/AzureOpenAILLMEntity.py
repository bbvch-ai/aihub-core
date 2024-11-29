from typing import Optional, Tuple

import tiktoken
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from llama_index.core.callbacks import CallbackManager, TokenCountingHandler
from llama_index.llms.azure_openai import AzureOpenAI
from mongoengine import DictField, EmbeddedDocumentField, FloatField, IntField, StringField

from lib_core.handlers.CostTracker import CostTracker
from lib_core.entities.LLM.chat.ChatLLMEntity import ChatLLMEntity, ChatLLMModelParameter


class AzureOpenAIParameter(ChatLLMModelParameter):
    logprobs = IntField(required=False)
    logit_bias = DictField(required=False)


class AzureOpenAILLMEntity(ChatLLMEntity):
    prompt_tokens_costs_per_thousand = FloatField(required=True)
    completion_tokens_costs_per_thousand = FloatField()
    api_version = StringField(required=True)

    default_parameter = EmbeddedDocumentField(AzureOpenAIParameter, required=True)

    def to_llama_index(self, model_parameter: Optional[AzureOpenAIParameter] = None) -> Tuple[AzureOpenAI, CostTracker]:
        tokenizer = tiktoken.encoding_for_model(self.name).encode
        token_counter = TokenCountingHandler(tokenizer=tokenizer)

        cost_tracker = CostTracker(
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
