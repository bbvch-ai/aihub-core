from abc import abstractmethod
from contextlib import asynccontextmanager
from typing import Optional, Tuple

from aihub_agent.displayers.EventDisplayer import EventDisplayer
from llama_index.core.llms import LLM
from pydantic import Field

from aihub_lib.generative_ai.llms.costs.LLMCostTracker import LLMCostTracker
from aihub_lib.generative_ai.llms.models.LLMConfig import LLMConfig, ModelParameter


class ChatLLMModelParameter(ModelParameter):
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

    default_parameter: ChatLLMModelParameter = Field(..., description="Default parameters for the chat-based LLM.")

    @abstractmethod
    def to_llama_index(self, model_parameter: Optional[ChatLLMModelParameter]) -> Tuple[LLM, LLMCostTracker]:
        pass

    @asynccontextmanager
    async def cost_reporting_llm(
        self, displayer: EventDisplayer, model_parameter: Optional[ChatLLMModelParameter] = None
    ):
        """
        Async context manager that yields an LLM configured with merged parameters.
        After the block, it reports costs to `displayer`.
        """
        llm, cost_tracker = self.to_llama_index(model_parameter)
        yield llm
        await displayer.display_llm_costs(self.name, cost_tracker)
