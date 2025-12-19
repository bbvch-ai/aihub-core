"""
Topic change detection for NamespaceSelectionAgent.

Detects when a user's query has changed topic significantly,
triggering re-evaluation of namespace selection.
"""

import logging

import numpy as np
from aihub_lib.generative_ai.resources.models.llm.EmbeddingModelConfig import EmbeddingModelConfig

logger = logging.getLogger(__name__)


def _cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    a = np.array(vec1)
    b = np.array(vec2)

    dot_product = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return float(dot_product / (norm_a * norm_b))


async def compute_query_embedding(query: str, embed_model_config: EmbeddingModelConfig) -> list[float]:
    """Compute embedding vector for a query string."""
    embed_model, _ = embed_model_config.to_llama_index()
    embedding = await embed_model.aget_text_embedding(query)
    return embedding


async def detect_topic_change(
    current_query: str,
    previous_embedding: list[float] | None,
    embed_model_config: EmbeddingModelConfig,
    threshold: float = 0.5,
) -> tuple[bool, list[float]]:
    """
    Detect if the current query represents a topic change from the previous query.

    Uses cosine similarity between query embeddings to detect topic changes.
    A similarity below the threshold indicates the topic has changed.

    Returns a tuple of (topic_changed, current_embedding).
    """
    current_embedding = await compute_query_embedding(current_query, embed_model_config)

    if previous_embedding is None:
        # First query - no previous topic to compare
        return False, current_embedding

    similarity = _cosine_similarity(current_embedding, previous_embedding)
    topic_changed = similarity < threshold

    if topic_changed:
        logger.debug(f"Topic change detected: similarity={similarity:.3f} < threshold={threshold}")
    else:
        logger.debug(f"Same topic: similarity={similarity:.3f} >= threshold={threshold}")

    return topic_changed, current_embedding
