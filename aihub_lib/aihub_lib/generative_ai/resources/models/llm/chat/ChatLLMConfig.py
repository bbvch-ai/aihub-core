from abc import abstractmethod
from contextlib import asynccontextmanager
from typing import AsyncIterator, Callable, List, Optional, Tuple

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

    temperature: float = Field(0.0, description="Controls randomness of the model output.")
    top_p: float = Field(1.0, description="Nucleus sampling threshold.")
    frequency_penalty: float = Field(0.0, description="Penalizes frequent tokens to reduce repetition.")
    max_tokens: Optional[int] = Field(None, description="Maximum number of tokens generated in the response.")
    presence_penalty: float = Field(0.0, description="Encourages new topics by penalizing repeated topics.")
    seed: int = Field(0, description="Seed for reproducibility, if supported by the model.")


class ChatLLMConfig(LLMConfig):
    """
    Configuration for a chat-based LLM, providing default parameters and a method
    to instantiate a chat LLM and cost tracker for llama_index.

    ### Why ChatLLMConfig?
    Chat models (like OpenAI's ChatGPT variants) often require parameters like temperature or max_tokens.
    With ChatLLMConfig, we integrate these parameters and the cost tracking mechanism in one place.
    """

    timeout: float = Field(30.0, description="Timeout for the model request in seconds (default: 30.0s).")
    default_parameter: ChatLLMParameter = Field(
        ..., description="Default parameters for the chat-based LLM.", default_factory=lambda: ChatLLMParameter()
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
