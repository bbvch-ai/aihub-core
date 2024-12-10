from abc import abstractmethod
from typing import Dict, Optional, Tuple

from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.core.llms import LLM

from pydantic import BaseModel

from lib_core.generative_ai.llms.costs.LLMCostTracker import LLMCostTracker


class ModelParameter(BaseModel):
    pass


class LLMConfig(BaseModel):
    name: str
    api_endpoint: str
    default_parameter: ModelParameter

    @abstractmethod
    def to_llama_index(self, model_parameter: Optional[ModelParameter]) -> Tuple[LLM | BaseEmbedding, LLMCostTracker]:
        pass

    def merge_model_params(self, model_parameter: Optional[ModelParameter]) -> Dict:
        model_params_dict = model_parameter.model_dump() if model_parameter else {}
        default_params_dict = self.default_parameter.model_dump()
        merged_params = {**default_params_dict, **model_params_dict}
        return {k: v for k, v in merged_params.items() if not k.startswith("_")}
