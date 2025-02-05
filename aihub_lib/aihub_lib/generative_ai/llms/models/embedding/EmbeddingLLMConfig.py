from abc import abstractmethod
from typing import Optional, Tuple

from llama_index.core.base.embeddings.base import BaseEmbedding
from pydantic import Field

from aihub_lib.generative_ai.llms.costs.LLMCostTracker import LLMCostTracker
from aihub_lib.generative_ai.llms.models.LLMConfig import LLMConfig, ModelParameter


class EmbeddingLLMModelParameter(ModelParameter):
    """
    Parameters specific to embedding models.

    ### Why EmbeddingLLMModelParameter?
    Embedding models may not have as many parameters as generative models, but by keeping a separate class,
    we maintain consistency and facilitate extension if embedding models require parameters in the future.
    """

    # Currently no additional fields, but can be extended in the future.
    pass


class EmbeddingLLMConfig(LLMConfig):
    """
    Configuration for an embedding model.

    ### Why EmbeddingLLMConfig?
    Embedding models produce vector representations of text. They may have different endpoints
    and possibly fewer parameters compared to chat models. This config ensures each embedding
    model can be integrated uniformly with llama_index and cost tracking.
    """

    default_parameter: EmbeddingLLMModelParameter = Field(
        ..., description="Default parameters for the embedding model.",
        default_factory=lambda: EmbeddingLLMModelParameter(),
    )

    @abstractmethod
    def to_llama_index(
        self, model_parameter: Optional[EmbeddingLLMModelParameter]
    ) -> Tuple[BaseEmbedding, LLMCostTracker]:
        pass
