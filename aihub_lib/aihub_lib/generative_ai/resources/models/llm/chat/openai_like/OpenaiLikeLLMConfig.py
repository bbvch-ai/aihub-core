from typing import Annotated, Callable, Dict, List, Optional, Tuple

from llama_index.core.callbacks import CallbackManager, TokenCountingHandler
from llama_index.llms.openai_like import OpenAILike
from pydantic import Field
from transformers import AutoTokenizer

from aihub_lib.generative_ai.resources.costs.LLMCostTracker import LLMCostTracker
from aihub_lib.generative_ai.resources.models.llm.chat.ChatLLMConfig import ChatLLMConfig, ChatLLMParameter


class OpenaiLikeLLMParameter(ChatLLMParameter):
    """
    Parameters for a self-hosted LLM using a local model via vLLM or another backend.

    ### Why OpenaiLikeLLMParameter?
    While many LLMs run as a managed service (like OpenAI or Azure),
    self-hosted models give you more control over the environment, models, and tuning.
    This parameter set allows specifying local logprob settings, biases, or other local backend features.
    """

    logprobs: Annotated[Optional[int], Field(None, description="Number of top tokens to return log probs for.")]
    logit_bias: Annotated[
        Optional[Dict[str, float]], Field(None, description="Adjust probabilities of specific tokens.")
    ]


class OpenaiLikeLLMConfig(ChatLLMConfig):
    """
    Configuration for a self-hosted LLM, potentially using vLLM or a local inference server.

    ### Why OpenaiLikeLLMConfig?
    Self-hosted models may not follow the same API patterns as OpenAI or Azure. They often:
    - Use a local endpoint (like http://localhost:port).
    - Provide chat or non-chat interfaces.
    - Require custom integration but still benefit from a consistent abstraction layer.

    This config ensures we can integrate a locally hosted LLM into llama_index with cost tracking and parameter merging.
    """

    context_size: Annotated[int, Field(..., description="Context window size (max tokens) supported by the model.")]
    is_function_calling_model: Annotated[bool, Field(..., description="True if the model supports function calling.")]
    is_chat_model: Annotated[bool, Field(True, description="True if the model uses a chat-based interface.")]

    default_parameter: Annotated[
        OpenaiLikeLLMParameter,
        Field(
            description="Default parameters for the self-hosted LLM.",
            default_factory=lambda: OpenaiLikeLLMParameter(),
        ),
    ]

    @property
    def tokenizer(self) -> Callable[[str], List[int]]:
        base_llm_name: str = self.name.replace("-GGUF", "").replace("-AWQ", "").replace("-bnb", "").replace("-4bit", "")
        return AutoTokenizer.from_pretrained(base_llm_name).encode

    def to_llama_index(
        self, model_parameter: Optional[OpenaiLikeLLMParameter] = None
    ) -> Tuple[OpenAILike, LLMCostTracker]:
        """
        Instantiate an OpenAILike model with local endpoint logic and a LLMCostTracker.

        This uses the OpenAILike wrapper since it mimics OpenAI-like APIs. The tokenizer is retrieved
        from the local model, and parameters are merged to configure the model's behavior.
        """
        token_counter = TokenCountingHandler(tokenizer=self.tokenizer)

        cost_tracker = LLMCostTracker(token_counter)
        additional_kwargs = self.merge_model_params(model_parameter)

        open_ai_like = OpenAILike(
            model=self.name,
            api_base=self.base_url,
            api_key=self.api_key or "fake",
            context_window=self.context_size,
            temperature=additional_kwargs.pop("temperature"),
            additional_kwargs=additional_kwargs,
            is_chat_model=self.is_chat_model,
            is_function_calling_model=self.is_function_calling_model,
            callback_manager=CallbackManager([token_counter]),
            timeout=self.timeout,
        )

        return open_ai_like, cost_tracker
