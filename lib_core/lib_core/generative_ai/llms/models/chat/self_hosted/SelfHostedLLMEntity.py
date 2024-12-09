from typing import Optional, Tuple, Dict

from llama_index.core.callbacks import CallbackManager, TokenCountingHandler
from llama_index.llms.openai_like import OpenAILike
from transformers import AutoTokenizer

from lib_core.generative_ai.llms.costs.CostTracker import CostTracker
from lib_core.generative_ai.llms.models.chat.ChatLLMConfig import ChatLLMConfig, ChatLLMModelParameter


class SelfHostedLLMParameter(ChatLLMModelParameter):
    logprobs: Optional[int] = None
    logit_bias: Optional[Dict[str, float]] = None


class SelfHostedLLMConfig(ChatLLMConfig):
    api_key: Optional[str] = None
    context_size: int
    is_chat_model: bool
    is_function_calling_model: bool

    default_parameter: SelfHostedLLMParameter

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
