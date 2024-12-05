from abc import abstractmethod
from typing import Optional, Tuple

from mongoengine import EmbeddedDocumentField, FloatField, IntField

from lib_core.entities import LLM
from lib_core.entities.LLM.LLMEntity import LLMEntity, ModelParameter
from lib_core.handlers.CostTracker import CostTracker


class ChatLLMModelParameter(ModelParameter):
    meta = {
        "allow_inheritance": True,
    }
    temperature = FloatField(required=False, default=0.0)
    top_p = FloatField(required=False, default=1.0)
    frequency_penalty = FloatField(required=False)
    max_tokens = IntField(required=False)
    presence_penalty = FloatField(required=False)
    seed = IntField(required=False)


class ChatLLMEntity(LLMEntity):
    meta = {
        "strict": True,
        "allow_inheritance": True,
    }

    default_parameter = EmbeddedDocumentField(ChatLLMModelParameter, required=True)

    @abstractmethod
    def to_llama_index(
        self, model_parameter: Optional[ChatLLMModelParameter]
    ) -> Tuple[LLM, CostTracker]:
        pass
