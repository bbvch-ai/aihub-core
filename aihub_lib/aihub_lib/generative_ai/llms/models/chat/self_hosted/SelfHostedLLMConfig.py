from typing import Annotated, Dict, Optional, Tuple

from llama_index.core.callbacks import CallbackManager, TokenCountingHandler
from llama_index.llms.openai_like import OpenAILike
from pydantic import Field
from transformers import AutoTokenizer

from aihub_lib.generative_ai.llms.costs.LLMCostTracker import LLMCostTracker
from aihub_lib.generative_ai.llms.models.chat.ChatLLMConfig import ChatLLMConfig, ChatLLMModelParameter


class SelfHostedLLMParameter(ChatLLMModelParameter):
    """
    Parameters for a self-hosted LLM using a local model via vLLM or another backend.

    ### Why SelfHostedLLMParameter?
    While many LLMs run as a managed service (like OpenAI or Azure),
    self-hosted models give you more control over the environment, models, and tuning.
    This parameter set allows specifying local logprob settings, biases, or other local backend features.
    """

    logprobs: Annotated[Optional[int], Field(None, description="Number of top tokens to return log probs for.")]
    logit_bias: Annotated[
        Optional[Dict[str, float]], Field(None, description="Adjust probabilities of specific tokens.")
    ]


class SelfHostedLLMConfig(ChatLLMConfig):
    """
    Configuration for a self-hosted LLM, potentially using vLLM or a local inference server.

    ### Why SelfHostedLLMConfig?
    Self-hosted models may not follow the same API patterns as OpenAI or Azure. They often:
    - Use a local endpoint (like http://localhost:port).
    - Provide chat or non-chat interfaces.
    - Require custom integration but still benefit from a consistent abstraction layer.

    This config ensures we can integrate a locally hosted LLM into llama_index with cost tracking and parameter merging.
    """

    api_key: Annotated[Optional[str], Field(None, description="API key if required by the local endpoint.")]
    context_size: Annotated[int, Field(..., description="Context window size (max tokens) supported by the model.")]
    is_chat_model: Annotated[bool, Field(..., description="True if the model uses a chat-based interface.")]
    is_function_calling_model: Annotated[bool, Field(..., description="True if the model supports function calling.")]
    tokenizer_name: Annotated[
        Optional[str], Field(None, description="Tokenizer name for the model. Defaults to model name.")
    ]

    default_parameter: Annotated[
        SelfHostedLLMParameter, Field(..., description="Default parameters for the self-hosted LLM.")
    ]

    def to_llama_index(
            self, model_parameter: Optional[SelfHostedLLMParameter] = None
    ) -> Tuple[OpenAILike, LLMCostTracker]:
        """
        Instantiate an OpenAILike model with local endpoint logic and a LLMCostTracker.

        This uses the OpenAILike wrapper since it mimics OpenAI-like APIs. The tokenizer is retrieved
        from the local model, and parameters are merged to configure the model's behavior.
        """
        tokenizer = AutoTokenizer.from_pretrained(self.tokenizer_name if self.tokenizer_name else self.name)
        token_counter = TokenCountingHandler(tokenizer=tokenizer)

        cost_tracker = LLMCostTracker(token_counter)
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
