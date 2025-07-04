from typing import Annotated, Callable, Dict, List, Optional, Tuple

import google.genai as genai
from llama_index.core.callbacks import CallbackManager, TokenCountingHandler
from llama_index.llms.openai_like import OpenAILike
from pydantic import Field

from aihub_lib.generative_ai.resources.costs.LLMCostTracker import LLMCostTracker
from aihub_lib.generative_ai.resources.models.llm.chat.ChatLLMConfig import ChatLLMConfig, ChatLLMParameter


class GeminiLLMParameter(ChatLLMParameter):
    """
    Parameters for gemini language models in openai compatible mode.

    ### Why GeminiLLMParameter?
    Googles Gemini can run in openai compatible mode, making it easy for us to use
    gemini and openai models interchangeably.
    """

    logprobs: Annotated[Optional[int], Field(None, description="Number of top tokens to return log probs for.")]
    logit_bias: Annotated[
        Optional[Dict[str, float]], Field(None, description="Adjust probabilities of specific tokens.")
    ]


class GeminiLLMConfig(ChatLLMConfig):
    """
    Configuration for gemini language model.
    """

    prompt_tokens_costs_per_thousand: Annotated[float, Field(description="Cost per thousand prompt tokens.")]
    completion_tokens_costs_per_thousand: Annotated[float, Field(description="Cost per thousand completion tokens.")]
    context_size: Annotated[int, Field(..., description="Context window size (max tokens) supported by the model.")]

    default_parameter: Annotated[
        GeminiLLMParameter,
        Field(
            description="Default parameters for the self-hosted LLM.",
            default_factory=lambda: GeminiLLMParameter(),
        ),
    ]

    @property
    def tokenizer(self) -> Callable[[str], List[int]]:
        client = genai.Client(
            api_key=self.api_key,
        )

        def token_counter(content: str) -> List[int]:
            response = client.models.count_tokens(model=f"models/{self.name}", contents=content)
            return [0] * response.total_tokens

        return token_counter

    def to_llama_index(self, model_parameter: Optional[GeminiLLMParameter] = None) -> Tuple[OpenAILike, LLMCostTracker]:
        """
        Instantiate an Gemini model in openai compatible mode and a LLMCostTracker.
        This uses the OpenAILike wrapper since it mimics OpenAI-like APIs.
        """
        token_counter = TokenCountingHandler(tokenizer=self.tokenizer)

        cost_tracker = LLMCostTracker(token_counter)
        additional_kwargs = self.merge_model_params(model_parameter)

        llm = OpenAILike(
            model=self.name,
            api_base=self.base_url,
            api_key=self.api_key,
            context_window=self.context_size,
            temperature=additional_kwargs.pop("temperature"),
            additional_kwargs=additional_kwargs,
            is_chat_model=True,
            is_function_calling_model=True,
            callback_manager=CallbackManager([token_counter]),
            timeout=self.timeout,
        )

        return llm, cost_tracker
