from dagster import Backoff, MetadataValue, OpExecutionContext, Output, ResourceParam, RetryPolicy, op
from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.core.schema import MetadataMode, TextNode
from openai import BadRequestError
from pydantic_core import ValidationError
from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import NODE_CONTENT_TYPE, PAGE

from swiss_ai_hub.pipeline.util.meta_utils import skipped_nodes_metadata_table


@op(
    code_version="v2",
    # Retries stay for transient failures (5xx, timeouts). A deterministic rejection no longer reaches them:
    # BadRequestError is handled below, so the op never re-raises it and never burns the retry budget on it.
    retry_policy=RetryPolicy(max_retries=6, delay=1, backoff=Backoff.EXPONENTIAL),
)
def embed_nodes(
    context: OpExecutionContext,
    nodes: list[TextNode],
    embedding_model: ResourceParam[BaseEmbedding],
) -> Output[list[TextNode]]:
    """
    Adds vector embeddings to a list of TextNodes, dropping the individual nodes the model refuses.

    A single unembeddable chunk used to fail the whole partition, so one oversized table cost the document
    every other node it had. Nodes the model rejects deterministically are now reported and skipped.
    """
    texts = [node.get_content(metadata_mode=MetadataMode.EMBED) for node in nodes]

    def embed_text_batch(batch_texts: list[str], offset: int) -> list[list[float] | None]:
        try:
            return list(embedding_model.get_text_embedding_batch(batch_texts))
        # BadRequestError is what an oversized chunk actually raises; ValidationError is what this op caught before
        # and could not be shown to be unreachable. Both are deterministic, so both are handled here rather than
        # left to exhaust the retry budget.
        except (BadRequestError, ValidationError) as rejection:
            if len(batch_texts) == 1:
                node = nodes[offset]
                context.log.error(
                    f"Embedding model rejected node {node.node_id} "
                    f"(page={node.metadata.get(PAGE)}, content_type={node.metadata.get(NODE_CONTENT_TYPE)}, "
                    f"{len(batch_texts[0])} chars): {rejection}"
                )
                return [None]
            half = len(batch_texts) // 2
            return embed_text_batch(batch_texts[:half], offset) + embed_text_batch(batch_texts[half:], offset + half)

    embeddings = embed_text_batch(texts, 0)

    embedded_nodes: list[TextNode] = []
    skipped_nodes: list[TextNode] = []
    for node, embedding in zip(nodes, embeddings, strict=True):
        if embedding is None:
            skipped_nodes.append(node)
        else:
            node.embedding = embedding
            embedded_nodes.append(node)

    if nodes and not embedded_nodes:
        # Tolerating a few bad chunks is the point of this op; tolerating a total refusal is not. An empty output
        # still stamps an unchanged DataVersion downstream, so the document would sit permanently unindexed behind
        # a green asset with nothing to trigger a retry.
        raise RuntimeError(
            f"Embedding model rejected all {len(nodes)} nodes - likely a model or gateway misconfiguration "
            f"rather than oversized content"
        )

    if skipped_nodes:
        context.log.warning(f"Skipped {len(skipped_nodes)} of {len(nodes)} nodes rejected by the embedding model")

    return Output(
        embedded_nodes,
        metadata={
            "Number of Embedded Nodes": MetadataValue.int(len(embedded_nodes)),
            "Number of Skipped Nodes": MetadataValue.int(len(skipped_nodes)),
            "Skipped Nodes": skipped_nodes_metadata_table(skipped_nodes),
        },
    )
