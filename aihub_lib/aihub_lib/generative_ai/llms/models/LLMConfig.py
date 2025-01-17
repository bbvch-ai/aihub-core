from abc import abstractmethod
from typing import Dict, Optional, Tuple, Union

from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.core.llms import LLM
from pydantic import BaseModel, Field

from aihub_lib.generative_ai.llms.costs.LLMCostTracker import LLMCostTracker


class ModelParameter(BaseModel):
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


class LLMConfig(BaseModel):
    """
    Configuration for a Language Model or embedding, including defaults and endpoints.

    ### Why LLMConfig?
    An application may rely on a variety of LLM backends (like OpenAI models or Azure endpoints),
    each with different defaults or endpoints. LLMConfig captures:
    - The model name
    - The API endpoint
    - Default parameters (via ModelParameter)

    This makes it easy to:
    - Switch between models without changing code.
    - Merge per-request parameters with defaults.
    - Instantiate LLM or embedding objects for llama_index consistently.
    """

    name: str = Field(..., description="The name of the LLM or embedding model.")
    api_endpoint: str = Field(..., description="The API endpoint to access the model.")
    default_parameter: ModelParameter = Field(..., description="The default parameters for the model.")

    @abstractmethod
    def to_llama_index(
        self, model_parameter: Optional[ModelParameter]
    ) -> Tuple[Union[LLM, BaseEmbedding], LLMCostTracker]:
        """
        Instantiate an LLM or embedding along with a cost tracker for llama_index.

        Subclasses should return:
        - An LLM or BaseEmbedding instance configured with merged parameters.
        - A LLMCostTracker instance to track token usage and costs.
        """
        pass

    def merge_model_params(self, model_parameter: Optional[ModelParameter]) -> Dict:
        """
        Merge default model parameters with provided ones. The merged dictionary excludes any
        fields starting with '_'.

        Returns:
            A dictionary of final model parameters to pass to the LLM or embedding.
        """
        model_params_dict = model_parameter.model_dump() if model_parameter else {}
        default_params_dict = self.default_parameter.model_dump()
        merged_params = {**default_params_dict, **model_params_dict}
        return {k: v for k, v in merged_params.items() if not k.startswith("_")}
