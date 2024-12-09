from abc import abstractmethod
from typing import Optional, Tuple

from lib_core.generative_ai.llms.costs.CostTracker import CostTracker
from lib_core.generative_ai.llms.models.LLMConfig import LLMConfig, ModelParameter


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
    def to_llama_index(self, model_parameter: Optional[ChatLLMModelParameter]) -> Tuple[LLMConfig, CostTracker]:
        pass
