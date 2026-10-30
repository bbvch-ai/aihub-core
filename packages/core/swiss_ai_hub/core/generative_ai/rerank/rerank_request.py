import logging
from collections.abc import Callable
from typing import Self

from llama_index.core.schema import MetadataMode, NodeWithScore
from pydantic import BaseModel, ConfigDict

from swiss_ai_hub.core.generative_ai.resources.models.llm.embedding_query_clamp import EmbeddingQueryClamp
from swiss_ai_hub.core.generative_ai.resources.tokenizers.measured_text_cut import MeasuredTextCut
from swiss_ai_hub.core.generative_ai.resources.tokenizers.model_token_budget import ModelTokenBudget

logger = logging.getLogger(__name__)

# Below this a query no longer carries the question it was asked with, so the longest documents give way instead.
MIN_QUERY_TOKENS = 256


class RerankRequest(BaseModel):
    """
    A query and its documents sized so every query/document pair fits the reranker's window.

    The reranker scores each pair in one window, and rejects the whole request with a 400 when one pair is over it,
    which costs the turn its reranking. Each document counts as it is actually sent, its metadata included, and
    nodes indexed before the ceiling was counted exactly (up to ~8.2k tokens) are cut for this request only.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True, frozen=True)

    query: str
    nodes: list[NodeWithScore]
    documents_cut: int = 0

    @classmethod
    def fit(cls, query: str, nodes: list[NodeWithScore], budget: ModelTokenBudget) -> Self:
        """Counting a long query and every document takes milliseconds, so async callers run this in a thread."""
        count = budget.tokenizer.count
        if not budget.exact:
            return cls(
                query=EmbeddingQueryClamp.clamp_to(query, EmbeddingQueryClamp.token_limit(budget), count), nodes=nodes
            )
        room = budget.usable_input_tokens
        longest_document = max(count(cls.document_text(node)) for node in nodes)
        if room - longest_document >= MIN_QUERY_TOKENS:
            return cls(query=EmbeddingQueryClamp.clamp_to(query, room - longest_document, count), nodes=nodes)
        fitted_query = EmbeddingQueryClamp.clamp_to(query, MIN_QUERY_TOKENS, count)
        document_limit = room - count(fitted_query)
        fitted_nodes = [cls._cut(node, document_limit, count) for node in nodes]
        documents_cut = sum(1 for node, fitted in zip(nodes, fitted_nodes, strict=True) if fitted is not node)
        if documents_cut:
            logger.warning(
                "Cut %d of %d documents to %d tokens for this rerank: the longest measured %d of the %d-token window",
                documents_cut,
                len(nodes),
                document_limit,
                longest_document,
                budget.max_input_tokens,
            )
        return cls(query=fitted_query, nodes=fitted_nodes, documents_cut=documents_cut)

    @staticmethod
    def document_text(node: NodeWithScore) -> str:
        """What the Cohere-compatible reranker client sends for a node."""
        return node.node.get_content(metadata_mode=MetadataMode.EMBED)

    @classmethod
    def _cut(cls, node: NodeWithScore, limit: int, count: Callable[[str], int]) -> NodeWithScore:
        if count(cls.document_text(node)) <= limit:
            return node
        original = node.node

        def sent_tokens(content: str) -> int:
            return count(original.model_copy(update={"text": content}).get_content(metadata_mode=MetadataMode.EMBED))

        head = MeasuredTextCut.longest_fitting_head(original.get_content(), limit, sent_tokens)
        return NodeWithScore(node=original.model_copy(update={"text": head}), score=node.score)
