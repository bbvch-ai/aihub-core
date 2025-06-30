from abc import abstractmethod
from contextlib import asynccontextmanager
from typing import Annotated, AsyncIterator, Callable, List, Optional, Tuple

from llama_index.core.llms import LLM
from pydantic import Field

from aihub_lib.displayers.EventDisplayer import EventDisplayer
from aihub_lib.generative_ai.resources.costs.LLMCostTracker import LLMCostTracker
from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig, LLMModelParameter


class ChatLLMParameter(LLMModelParameter):
    """
    Parameters for a chat-based LLM.

    ### Why ChatLLMModelParameter?
    Chat-oriented models might need parameters controlling randomness, token limits, or repetition.
    By defining them here, we standardize parameter handling and ensure easy customization.
    """

    temperature: Annotated[float, Field(description="Controls randomness of the model output.")] = 0.0
    top_p: Annotated[float, Field(description="Nucleus sampling threshold.")] = 1.0
    frequency_penalty: Annotated[float, Field(description="Penalizes frequent tokens to reduce repetition.")] = 0.0
    max_tokens: Annotated[Optional[int], Field(description="Maximum number of tokens generated in the response.")] = (
        None
    )
    presence_penalty: Annotated[float, Field(description="Encourages new topics by penalizing repeated topics.")] = 0.0
    seed: Annotated[int, Field(description="Seed for reproducibility, if supported by the model.")] = 0


class ChatLLMConfig(LLMConfig):
    """
    Configuration for a chat-based LLM, providing default parameters and a method
    to instantiate a chat LLM and cost tracker for llama_index.

    ### Why ChatLLMConfig?
    Chat models (like OpenAI's ChatGPT variants) often require parameters like temperature or max_tokens.
    With ChatLLMConfig, we integrate these parameters and the cost tracking mechanism in one place.
    """

    timeout: Annotated[float, Field(description="Timeout for the model request in seconds (default: 30.0s).")] = 30.0
    default_parameter: Annotated[ChatLLMParameter, Field(description="Default parameters for the chat-based LLM.")] = (
        ChatLLMParameter()
    )

    @property
    @abstractmethod
    def tokenizer(self) -> Callable[[str], List[int]]:
        pass

    @abstractmethod
    def to_llama_index(self, model_parameter: Optional[ChatLLMParameter] = None) -> Tuple[LLM, LLMCostTracker]:
        pass

    @asynccontextmanager
    async def cost_reporting_llm(
        self,
        displayer: EventDisplayer,
        model_parameter: Optional[ChatLLMParameter] = None,
        system_prompt: Optional[str] = None,
    ) -> AsyncIterator[LLM]:
        """
        Async context manager that yields an LLM configured with merged parameters and a system prompt.
        After the block, it reports costs to `displayer`.
        """
        llm, cost_tracker = self.to_llama_index(model_parameter)
        if system_prompt:
            llm.system_prompt = system_prompt
        yield llm
        await displayer.display_llm_costs(self.name, cost_tracker)
