from typing import Annotated, Literal

from llama_index.core.callbacks import CallbackManager, TokenCountingHandler
from llama_index.embeddings.openai_like import OpenAILikeEmbedding
from opentelemetry.propagate import inject
from pydantic import BaseModel, Field

from aihub_lib.generative_ai.resources.costs.LLMCostTracker import LLMCostTracker
from aihub_lib.generative_ai.resources.models.llm.LiteLLMBase import LiteLLMBase
from aihub_lib.infrastructure.litellm.LiteLLMProxySettings import LiteLLMProxySettings


class EmbeddingLLMParameter(BaseModel):
    """
    Parameters specific to embedding models.

    ### Why EmbeddingLLMModelParameter?
    Embedding models may not have as many parameters as generative models, but by keeping a separate class,
    we maintain consistency and facilitate extension if embedding models require parameters in the future.
    """

    max_retries: int = Field(default=10, description="Maximum number of retries.", ge=0)
    timeout: float = Field(default=60.0, description="Timeout for each request.", ge=0)
    encoding_format: Annotated[
        Literal["float", "base64"] | None,
        Field(description="Format of the returned embeddings. Defaults to 'float'."),
    ] = "float"
    dimensions: Annotated[
        int | None,
        Field(
            description="Number of dimensions for output embeddings. Supported in text-embedding-3 and later models."
        ),
    ] = None


class EmbeddingModelConfig(LiteLLMBase[OpenAILikeEmbedding]):
    """
    Configuration for an embedding model.

    ### Why EmbeddingModelConfig?
    Embedding models produce vector representations of text. They may have different endpoints
    and possibly fewer parameters compared to chat models. This config ensures each embedding
    model can be integrated uniformly with llama_index and cost tracking.
    """

    model_name: Annotated[str, Field(description="Name of the embedding model.")]
    default_parameter: Annotated[
        EmbeddingLLMParameter,
        Field(
            description="Default parameters for the embedding model.",
        ),
    ] = EmbeddingLLMParameter()

    def to_llama_index(self) -> tuple[OpenAILikeEmbedding, LLMCostTracker]:
        config = LiteLLMProxySettings()
        model_info = self.get_model_info()

        token_counter = TokenCountingHandler(tokenizer=self.token_counter)
        cost_tracker = LLMCostTracker(
            token_counter=token_counter,
            embedding_tokens_costs_per_thousand=model_info["model_info"]["input_cost_per_token"] * 1000,
        )

        default_headers = {}
        inject(default_headers)

        open_ai_like_embedding = OpenAILikeEmbedding(
            model_name=self.model_name,
            api_base=config.BASE_URL,
            api_key=config.API_KEY.get_secret_value(),
            max_retries=self.default_parameter.max_retries,
            callback_manager=CallbackManager([token_counter]),
            timeout=self.default_parameter.timeout,
            default_headers=default_headers,
            dimensions=self.default_parameter.dimensions,
        )

        return open_ai_like_embedding, cost_tracker
