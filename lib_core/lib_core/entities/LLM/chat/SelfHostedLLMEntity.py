from typing import Optional, Tuple

from llama_index.core.callbacks import CallbackManager, TokenCountingHandler
from llama_index.llms.openai_like import OpenAILike
from mongoengine import (
    BooleanField,
    DictField,
    EmbeddedDocumentField,
    IntField,
    StringField,
)
from transformers import AutoTokenizer

from lib_core.entities.LLM.chat.ChatLLMEntity import (
    ChatLLMEntity,
    ChatLLMModelParameter,
)
from lib_core.handlers.CostTracker import CostTracker


class SelfHostedLLMParameter(ChatLLMModelParameter):
    logprobs = IntField(required=False)
    logit_bias = DictField(required=False)


class SelfHostedLLMEntity(ChatLLMEntity):
    api_key = StringField(required=False)
    context_size = IntField(required=True)
    is_chat_model = BooleanField(required=True)
    is_function_calling_model = BooleanField(required=True)

    default_parameter = EmbeddedDocumentField(SelfHostedLLMParameter, required=True)

    def to_llama_index(
        self, model_parameter: Optional[SelfHostedLLMParameter] = None
    ) -> Tuple[OpenAILike, CostTracker]:
        tokenizer = AutoTokenizer.from_pretrained(self.name)
        token_counter = TokenCountingHandler(tokenizer=tokenizer)

        cost_tracker = CostTracker(token_counter)
        additional_kwargs = self.merge_model_params(model_parameter)

        open_ai_like = OpenAILike(
            model=self.name,
            api_base=self.api_endpoint,
            api_key=self.api_key,
            context_window=self.context_size,
            temperature=additional_kwargs.pop("temperature"),
            additional_kwargs=additional_kwargs,
            is_chat_model=self.is_chat_model,
            is_function_calling_model=self.is_function_calling_model,
            callback_manager=CallbackManager([token_counter]),
        )

        return open_ai_like, cost_tracker
