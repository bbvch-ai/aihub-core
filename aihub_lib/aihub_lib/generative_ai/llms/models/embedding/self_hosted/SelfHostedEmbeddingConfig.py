from typing import Optional, Tuple, Annotated

from llama_index.core.callbacks import CallbackManager, TokenCountingHandler
from llama_index.embeddings.text_embeddings_inference import TextEmbeddingsInference
from transformers import AutoTokenizer
from pydantic import Field

from aihub_lib.generative_ai.llms.costs.LLMCostTracker import LLMCostTracker
from aihub_lib.generative_ai.llms.models.embedding.EmbeddingLLMConfig import EmbeddingLLMConfig, EmbeddingLLMModelParameter


class SelfHostedEmbeddingParameter(EmbeddingLLMModelParameter):
    """
    Parameters for a self-hosted embedding model, possibly using text-embedding-inference or another local inference server.

    ### Why SelfHostedEmbeddingParameter?
    Self-hosted embedding services might allow instructions, truncation toggles, or other special parameters.
    Storing them here keeps configuration unified and flexible.
    """

    text_instruction: Annotated[Optional[str], Field("", description="Instruction to apply when embedding text.")]
    query_instruction: Annotated[Optional[str], Field("", description="Instruction to apply when embedding a query.")]
    truncate_text: Annotated[bool, Field(False, description="If True, truncate text to model's max length." )]


class SelfHostedEmbeddingConfig(EmbeddingLLMConfig):
    """
    Configuration for a self-hosted embedding model using text-embedding-inference or similar backends.

    ### Why SelfHostedEmbeddingConfig?
    Self-hosted embeddings differ from cloud-provided ones. This config allows:
    - Using local endpoints.
    - Setting custom instructions or behaviors.
    - Integrating with llama_index embeddings via the TextEmbeddingsInference wrapper.
    """

    api_key: Annotated[Optional[str], Field(None, description="API key if required by the local embedding endpoint.")]
    timeout: Annotated[int, Field(60, description="HTTP request timeout in seconds.")]
    embed_batch_size: Annotated[int, Field(32, description="Number of texts to embed in one batch.")]

    default_parameter: Annotated[SelfHostedEmbeddingParameter, Field(..., description="Default parameters for the self-hosted embedding model.")]

    def to_llama_index(
        self, model_parameter: Optional[SelfHostedEmbeddingParameter]
    ) -> Tuple[TextEmbeddingsInference, LLMCostTracker]:
        """
        Instantiate a TextEmbeddingsInference object and LLMCostTracker for self-hosted embeddings.

        Parameters are merged to configure instructions and truncation options.
        """
        tokenizer = AutoTokenizer.from_pretrained(self.name)
        token_counter = TokenCountingHandler(tokenizer=tokenizer)

        cost_tracker = LLMCostTracker(token_counter)
        additional_kwargs = self.merge_model_params(model_parameter)

        text_embedding_inference = TextEmbeddingsInference(
            model_name=self.name,
            base_url=self.api_endpoint,
            text_instruction=additional_kwargs.get("text_instruction"),
            query_instruction=additional_kwargs.get("query_instruction"),
            truncate_text=additional_kwargs.get("truncate_text"),
            timeout=self.timeout,
            embed_batch_size=self.embed_batch_size,
            callback_manager=CallbackManager([token_counter]),
        )

        return text_embedding_inference, cost_tracker
