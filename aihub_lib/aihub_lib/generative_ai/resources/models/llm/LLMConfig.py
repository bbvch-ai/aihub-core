from abc import abstractmethod
from typing import Dict, Optional, Tuple, Union

from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.core.llms import LLM
from pydantic import Field

from aihub_lib.generative_ai.resources.costs.LLMCostTracker import LLMCostTracker
from aihub_lib.generative_ai.resources.models.ResourceConfig import ResourceConfig, ResourceParameter


class LLMModelParameter(ResourceParameter):
    """
    A base class for model parameters used to configure LLMs or embeddings.

    ### Why ModelParameter?
    Different LLMs or embedding models may require parameters (like temperature, top_p, max_tokens)
    to shape their output. By encapsulating these parameters in a typed model, we gain:
    - Validation and defaults via Pydantic.
    - Easy merging of default and per-request parameters.

    Subclasses should define fields relevant to their respective models.
    """

    pass


class LLMConfig(ResourceConfig):
    default_parameter: LLMModelParameter = Field(..., description="The default parameters for the model.")

    @abstractmethod
    def to_llama_index(
        self, model_parameter: Optional[LLMModelParameter]
    ) -> Tuple[Union[LLM, BaseEmbedding], LLMCostTracker]:
        """
        Instantiate an LLM or embedding along with a cost tracker for llama_index.

        Subclasses should return:
        - An LLM or BaseEmbedding instance configured with merged parameters.
        - A LLMCostTracker instance to track token usage and costs.
        """
        pass

    def merge_model_params(self, model_parameter: Optional[LLMModelParameter] = None) -> Dict:
        """
        Merge default model parameters with provided ones. The merged dictionary excludes any
        fields starting with '_'.
        """
        model_params_dict = model_parameter.model_dump() if model_parameter else {}
        default_params_dict = self.default_parameter.model_dump()
        merged_params = {**default_params_dict, **model_params_dict}
        return {k: v for k, v in merged_params.items() if not k.startswith("_")}
