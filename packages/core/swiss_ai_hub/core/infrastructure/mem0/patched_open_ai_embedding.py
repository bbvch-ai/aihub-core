import logging
from typing import Literal, Self, override

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
    def from_embedding(cls, embedding: OpenAIEmbedding) -> Self:
        """Wrap an existing OpenAIEmbedding instance, preserving its config and client."""
        instance = cls.__new__(cls)
        instance.config = embedding.config
        instance.client = embedding.client
        return instance

    @override
    def embed(self, text, memory_action: Literal["add", "search", "update"] | None = None):
        text = text.replace("\n", " ")
        return self.client.embeddings.create(input=[text], model=self.config.model).data[0].embedding
