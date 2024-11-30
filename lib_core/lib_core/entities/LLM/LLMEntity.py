from abc import abstractmethod
from typing import Dict, Optional, Tuple

from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.core.llms import LLM
from mongoengine import Document, EmbeddedDocument, EmbeddedDocumentField, IntField, StringField

from lib_core.handlers.CostTracker import CostTracker


class ModelParameter(EmbeddedDocument):
    meta = {
        "allow_inheritance": True,
    }


class LLMEntity(Document):
    meta = {
        "collection": "llms",
        "strict": True,
        "allow_inheritance": True,
    }
    version = IntField(default=1, db_field="_version")
    name = StringField(required=True)
    api_endpoint = StringField(required=True)

    default_parameter = EmbeddedDocumentField(ModelParameter, required=True)

    @abstractmethod
    def to_llama_index(self, model_parameter: Optional[ModelParameter]) -> Tuple[LLM | BaseEmbedding, CostTracker]:
        pass

    def merge_model_params(self, model_parameter: Optional[ModelParameter]) -> Dict:
        model_params_dict = model_parameter.to_mongo().to_dict() if model_parameter else {}
        default_params_dict = self.default_parameter.to_mongo().to_dict()
        merged_params = {**default_params_dict, **model_params_dict}
        return {k: v for k, v in merged_params.items() if not k.startswith("_")}
