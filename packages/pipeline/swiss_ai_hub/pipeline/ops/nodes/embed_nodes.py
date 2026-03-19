from dagster import Backoff, ResourceParam, RetryPolicy, op
from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.core.schema import MetadataMode, TextNode
from pydantic_core import ValidationError


@op(
    code_version="v1",
    retry_policy=RetryPolicy(max_retries=6, delay=1, backoff=Backoff.EXPONENTIAL),
)
def embed_nodes(
    nodes: list[TextNode],
    embedding_model: ResourceParam[BaseEmbedding],
) -> list[TextNode]:
    """Adds vector embeddings to a list of TextNodes using the provided embedding model."""
    texts = [node.get_content(metadata_mode=MetadataMode.EMBED) for node in nodes]

    def embed_text_batch(_texts: list[str]) -> list[list[float]]:
        try:
            return embedding_model.get_text_embedding_batch(_texts)
        except ValidationError as _:
            if len(_texts) == 1:
                raise
            batch_one = embed_text_batch(_texts[: len(_texts) // 2])
            batch_two = embed_text_batch(_texts[len(_texts) // 2 :])
            return batch_one + batch_two

    embeddings = embed_text_batch(texts)

    for node, embedding in zip(nodes, embeddings):
        node.embedding = embedding

    return nodes
