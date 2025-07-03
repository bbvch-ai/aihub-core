from abc import abstractmethod
from typing import Annotated, Optional, Tuple

from llama_index.core.base.embeddings.base import BaseEmbedding
from pydantic import Field

from aihub_lib.generative_ai.resources.costs.LLMCostTracker import LLMCostTracker
from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig, LLMModelParameter


class EmbeddingLLMParameter(LLMModelParameter):
    """
    Parameters specific to embedding models.

    ### Why EmbeddingLLMModelParameter?
    Embedding models may not have as many parameters as generative models, but by keeping a separate class,
    we maintain consistency and facilitate extension if embedding models require parameters in the future.
    """

    pass


class EmbeddingLLMConfig(LLMConfig):
    """
    Configuration for an embedding model.

    ### Why EmbeddingLLMConfig?
    Embedding models produce vector representations of text. They may have different endpoints
    and possibly fewer parameters compared to chat models. This config ensures each embedding
    model can be integrated uniformly with llama_index and cost tracking.
    """

    # Keeping Field() explicitly for default_factory
    default_parameter: Annotated[
        EmbeddingLLMParameter,
        Field(
            description="Default parameters for the embedding model.",
        ),
    ] = EmbeddingLLMParameter()

    @abstractmethod
    def to_llama_index(
        self, model_parameter: Optional[EmbeddingLLMParameter] = None
    ) -> Tuple[BaseEmbedding, LLMCostTracker]:
        pass
