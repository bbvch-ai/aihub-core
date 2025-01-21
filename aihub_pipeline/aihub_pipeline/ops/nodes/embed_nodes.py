from typing import List

from dagster import Backoff, ResourceParam, RetryPolicy, op
from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.core.schema import TextNode


@op(
    code_version="v1",
    retry_policy=RetryPolicy(max_retries=6, delay=1, backoff=Backoff.EXPONENTIAL),
)
def embed_nodes(
    nodes: List[TextNode],
    embedding_model: ResourceParam[BaseEmbedding],
) -> List[TextNode]:
    """Adds vector embeddings to a list of TextNodes using the provided embedding model."""
    embeddings = embedding_model.get_text_embedding_batch([node.get_text() for node in nodes])
    for node, embedding in zip(nodes, embeddings):
        node.embedding = embedding

    return nodes
