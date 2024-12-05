from typing import Optional, Tuple

from llama_index.core.callbacks import CallbackManager, TokenCountingHandler
from llama_index.embeddings.text_embeddings_inference import TextEmbeddingsInference
from mongoengine import BooleanField, EmbeddedDocumentField, IntField, StringField
from transformers import AutoTokenizer

from lib_core.entities.LLM.embedding.EmbeddingLLMEntity import (
    EmbeddingLLMEntity,
    EmbeddingLLMModelParameter,
)
from lib_core.handlers.CostTracker import CostTracker


class SelfHostedEmbeddingParameter(EmbeddingLLMModelParameter):
    text_instruction = StringField(required=False, default="")
    query_instruction = StringField(required=False, default="")
    truncate_text = BooleanField(required=False, default=False)


class SelfHostedEmbeddingEntity(EmbeddingLLMEntity):
    api_key = StringField(required=False)
    timeout = IntField(required=False, default=60)
    embed_batch_size = IntField(required=False, default=32)

    default_parameter = EmbeddedDocumentField(
        SelfHostedEmbeddingParameter, required=True
    )

    def to_llama_index(
        self, model_parameter: Optional[SelfHostedEmbeddingParameter]
    ) -> Tuple[TextEmbeddingsInference, CostTracker]:
        tokenizer = AutoTokenizer.from_pretrained(self.name)
        token_counter = TokenCountingHandler(tokenizer=tokenizer)

        cost_tracker = CostTracker(token_counter)
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
