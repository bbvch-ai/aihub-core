from typing import Optional, Tuple

from llama_index.core.callbacks import CallbackManager, TokenCountingHandler
from llama_index.embeddings.text_embeddings_inference import TextEmbeddingsInference
from transformers import AutoTokenizer

from lib_core.generative_ai.llms.costs.LLMCostTracker import LLMCostTracker
from lib_core.generative_ai.llms.models.embedding.EmbeddingLLMConfig import EmbeddingLLMConfig, \
    EmbeddingLLMModelParameter


class SelfHostedEmbeddingParameter(EmbeddingLLMModelParameter):
    text_instruction: Optional[str] = ""
    query_instruction: Optional[str] = ""
    truncate_text: bool = False


class SelfHostedEmbeddingConfig(EmbeddingLLMConfig):
    api_key: Optional[str] = None
    timeout: int = 60
    embed_batch_size: int = 32

    default_parameter: SelfHostedEmbeddingParameter

    def to_llama_index(
        self, model_parameter: Optional[SelfHostedEmbeddingParameter]
    ) -> Tuple[TextEmbeddingsInference, LLMCostTracker]:
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
