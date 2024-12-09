from abc import abstractmethod
from typing import Optional, Tuple

from llama_index.core.base.embeddings.base import BaseEmbedding

from lib_core.generative_ai.llms.costs.CostTracker import CostTracker
from lib_core.generative_ai.llms.models.LLMConfig import LLMConfig, ModelParameter


class EmbeddingLLMModelParameter(ModelParameter):
    pass


class EmbeddingLLMConfig(LLMConfig):
    default_parameter: EmbeddingLLMModelParameter

    @abstractmethod
    def to_llama_index(
        self, model_parameter: Optional[EmbeddingLLMModelParameter]
    ) -> Tuple[BaseEmbedding, CostTracker]:
        pass
