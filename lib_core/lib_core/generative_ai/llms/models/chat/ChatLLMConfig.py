from abc import abstractmethod
from contextlib import contextmanager, asynccontextmanager
from typing import Optional, Tuple

from llama_index.core.llms import LLM

from agents_core.displayers.EventDisplayer import EventDisplayer
from lib_core.generative_ai.llms.costs.LLMCostTracker import LLMCostTracker
from lib_core.generative_ai.llms.models.LLMConfig import ModelParameter, LLMConfig


class ChatLLMModelParameter(ModelParameter):
    temperature: float = 0.0
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    max_tokens: Optional[int] = None
    presence_penalty: float = 0.0
    seed: int = 0


class ChatLLMConfig(LLMConfig):
    default_parameter: ChatLLMModelParameter

    @abstractmethod
    def to_llama_index(self, model_parameter: Optional[ChatLLMModelParameter]) -> Tuple[LLM, LLMCostTracker]:
        pass

    @asynccontextmanager
    async def cost_reporting_llm(self, displayer: EventDisplayer, model_parameter: Optional[ChatLLMModelParameter] = None):
        llm, cost_tracker = self.to_llama_index(model_parameter)
        yield llm
        await displayer.display_llm_costs(self.name, cost_tracker)