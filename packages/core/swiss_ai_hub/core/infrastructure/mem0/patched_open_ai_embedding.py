import logging
from typing import Literal, Self, override

import tiktoken
from mem0.embeddings.openai import OpenAIEmbedding

logger = logging.getLogger(__name__)


class PatchedOpenAIEmbedding(OpenAIEmbedding):
    """
    Patches mem0's OpenAIEmbedding to not pass the dimensions parameter.

    Some providers (e.g. Infomaniak / Swiss LLM Cloud) do not support the
    dimensions parameter for embedding models. mem0 always passes it, so
    this patch removes it from the API call.
    """

    @classmethod
    def from_embedding(cls, embedding: OpenAIEmbedding, max_input_tokens: int | None = None) -> Self:
        """Wrap an existing embedding client and retain a conservative input budget."""
        instance = cls.__new__(cls)
        instance.config = embedding.config
        instance.client = embedding.client
        instance._max_input_tokens = max_input_tokens
        instance._tokenizer = tiktoken.get_encoding("cl100k_base")
        return instance

    @override
    def embed(self, text, memory_action: Literal["add", "search", "update"] | None = None):
        text = text.replace("\n", " ")
        if self._max_input_tokens is not None:
            text = self._tokenizer.decode(self._tokenizer.encode(text)[: self._max_input_tokens])
        return self.client.embeddings.create(input=[text], model=self.config.model).data[0].embedding
