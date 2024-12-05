from abc import abstractmethod
from typing import Optional, Tuple

from llama_index.core.base.embeddings.base import BaseEmbedding
from mongoengine import EmbeddedDocumentField

from lib_core.entities.LLM.LLMEntity import LLMEntity, ModelParameter
from lib_core.handlers.CostTracker import CostTracker


class EmbeddingLLMModelParameter(ModelParameter):
    meta = {
        "allow_inheritance": True,
    }
    pass


class EmbeddingLLMEntity(LLMEntity):
    meta = {
        "strict": True,
        "allow_inheritance": True,
    }

    default_parameter = EmbeddedDocumentField(EmbeddingLLMModelParameter, required=True)

    @abstractmethod
    def to_llama_index(
        self, model_parameter: Optional[EmbeddingLLMModelParameter]
    ) -> Tuple[BaseEmbedding, CostTracker]:
        pass
