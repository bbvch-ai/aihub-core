"""The knowledge capability and the RAG agent rerank with the turn's query as is, and a chat with an attached file
inlines the document into it. The reranker rejects an oversized query plus document pair with a 400 (20922 tokens
against an 8192 window), so the clamp has to sit in `rerank_nodes` where every caller passes through."""

from unittest.mock import MagicMock, patch

import pytest
from llama_index.core.utils import get_tokenizer

from swiss_ai_hub.core.generative_ai.document.types.ingested_node import IngestedNode
from swiss_ai_hub.core.generative_ai.rerank.rerank_nodes import rerank_nodes
from swiss_ai_hub.core.generative_ai.resources.models.llm.embedding_query_clamp import QUERY_BUDGET_SAFETY_FACTOR
from swiss_ai_hub.core.generative_ai.resources.models.llm.reranking_model_config import RerankingModelConfig
from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import NODE_CONTENT_TYPE_TEXT

MODEL_CONFIG = "swiss_ai_hub.core.generative_ai.resources.models.llm.embedding_query_clamp.EmbeddingModelConfig"
WINDOW = 8192


def _node() -> IngestedNode:
    return IngestedNode(
        id="node-1",
        content="Termination requires 30 days written notice.",
        content_type=NODE_CONTENT_TYPE_TEXT,
        document_id="doc-1",
        source="doc-1",
        namespace="ns",
        document_title="Contract",
        created_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z",
        inserted_at="2026-01-01T00:00:00Z",
        metadata={},
    )


def _capturing_reranker() -> tuple[MagicMock, dict]:
    captured: dict = {}
    service = MagicMock()

    def postprocess_nodes(query_str, nodes):
        captured["query_str"] = query_str
        return nodes

    service.postprocess_nodes.side_effect = postprocess_nodes
    return service, captured


@pytest.mark.asyncio
async def test_document_sized_query_is_clamped_before_reranking():
    question = "What does the attached contract say about termination?"
    query = ("Contract clause text. " * 6000) + question
    service, captured = _capturing_reranker()

    with (
        patch.object(RerankingModelConfig, "to_llama_index", return_value=(service, MagicMock())),
        patch(MODEL_CONFIG) as config_cls,
    ):
        config_cls.return_value.get_model_info.return_value = {"model_info": {"max_input_tokens": WINDOW}}
        result = await rerank_nodes([_node()], query, RerankingModelConfig(model_name="reranker/bge", top_n=5))

    assert len(result) == 1
    assert len(get_tokenizer()(captured["query_str"])) <= int(WINDOW * QUERY_BUDGET_SAFETY_FACTOR)
    assert captured["query_str"].endswith(question)


@pytest.mark.asyncio
async def test_short_query_reaches_the_reranker_unchanged():
    query = "What is the retention period?"
    service, captured = _capturing_reranker()

    with (
        patch.object(RerankingModelConfig, "to_llama_index", return_value=(service, MagicMock())),
        patch(MODEL_CONFIG) as config_cls,
    ):
        await rerank_nodes([_node()], query, RerankingModelConfig(model_name="reranker/bge", top_n=5))

    assert captured["query_str"] is query
    config_cls.assert_not_called()
