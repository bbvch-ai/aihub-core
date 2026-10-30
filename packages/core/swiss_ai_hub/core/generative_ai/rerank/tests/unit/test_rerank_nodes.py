"""The knowledge capability and the RAG agent rerank with the turn's query as is, and a chat with an attached file
inlines the document into it. The reranker rejects an oversized query plus document pair with a 400 (20922 tokens
against an 8192 window), which costs the whole turn its reranking, so the request is sized in `rerank_nodes`, where
every caller passes through. Nodes indexed before the ceiling was counted exactly reach ~8.2k tokens and are never
re-indexed, so the document side is sized too."""

from unittest.mock import MagicMock, patch

import pytest
from llama_index.core.utils import get_tokenizer

from swiss_ai_hub.core.generative_ai.document.types.ingested_node import IngestedNode
from swiss_ai_hub.core.generative_ai.rerank.rerank_nodes import rerank_nodes
from swiss_ai_hub.core.generative_ai.rerank.rerank_request import MIN_QUERY_TOKENS, RerankRequest
from swiss_ai_hub.core.generative_ai.resources.models.llm.embedding_query_clamp import QUERY_BUDGET_SAFETY_FACTOR
from swiss_ai_hub.core.generative_ai.resources.models.llm.reranking_model_config import RerankingModelConfig
from swiss_ai_hub.core.generative_ai.resources.tokenizers.model_token_budget import ModelTokenBudget
from swiss_ai_hub.core.generative_ai.resources.tokenizers.model_tokenizer import ModelTokenizer
from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import NODE_CONTENT_TYPE_TEXT

WINDOW = 8192
PAIR_OVERHEAD = 4
DECLARED = {"mode": "rerank", "max_input_tokens": WINDOW, "aihub_tokenizer": "bge-m3", "aihub_input_overhead_tokens": 4}
UNDECLARED = {"mode": "rerank", "max_input_tokens": WINDOW}
QUESTION = "What does the attached contract say about termination?"


def _node(node_id: str = "node-1", content: str = "Termination requires 30 days written notice.") -> IngestedNode:
    return IngestedNode(
        id=node_id,
        content=content,
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


def _legacy_node(node_id: str = "legacy") -> IngestedNode:
    """A node as the 0.85 x 8192 tiktoken ceiling let it through: about 8.2k bge-m3 tokens of code."""
    tokenizer = ModelTokenizer.shared("bge-m3")
    content = ""
    line = "    result = compute_total(items, discount=0.15)  # apply the seasonal rebate\n"
    while tokenizer.count(content) < 8200:
        content += line
    return _node(node_id, content)


def _capturing_reranker() -> tuple[MagicMock, dict]:
    captured: dict = {}
    service = MagicMock()

    def postprocess_nodes(query_str, nodes):
        captured["query_str"] = query_str
        captured["nodes"] = nodes
        return list(reversed(nodes))

    service.postprocess_nodes.side_effect = postprocess_nodes
    return service, captured


async def _rerank(nodes: list[IngestedNode], query: str, model_info: dict) -> tuple[list[IngestedNode], dict]:
    service, captured = _capturing_reranker()
    with (
        patch.object(RerankingModelConfig, "to_llama_index", return_value=(service, MagicMock())),
        patch.object(RerankingModelConfig, "get_model_info", return_value={"model_info": model_info}),
    ):
        result = await rerank_nodes(nodes, query, RerankingModelConfig(model_name="reranker/bge", top_n=5))
    return result, captured


def _sent_pair_tokens(captured: dict) -> list[int]:
    tokenizer = ModelTokenizer.shared("bge-m3")
    query_tokens = tokenizer.count(captured["query_str"])
    return [
        PAIR_OVERHEAD + query_tokens + tokenizer.count(RerankRequest.document_text(node)) for node in captured["nodes"]
    ]


@pytest.mark.asyncio
async def test_undeclared_reranker_keeps_half_the_window_in_tiktoken():
    query = ("Contract clause text. " * 6000) + QUESTION

    result, captured = await _rerank([_node()], query, UNDECLARED)

    assert len(result) == 1
    assert len(get_tokenizer()(captured["query_str"])) <= int(WINDOW * QUERY_BUDGET_SAFETY_FACTOR)
    assert captured["query_str"].endswith(QUESTION)


@pytest.mark.asyncio
async def test_short_query_reaches_the_reranker_unchanged():
    query = "What is the retention period?"

    _, captured = await _rerank([_node()], query, DECLARED)

    assert captured["query_str"] is query


@pytest.mark.asyncio
async def test_declared_reranker_leaves_the_query_the_room_the_longest_document_leaves():
    query = ("Contract clause text. " * 6000) + QUESTION
    nodes = [_node("short"), _node("long", "Clause. " * 1500)]

    _, captured = await _rerank(nodes, query, DECLARED)

    pairs = _sent_pair_tokens(captured)
    assert max(pairs) <= WINDOW
    assert max(pairs) > WINDOW - 50
    assert captured["query_str"].endswith(QUESTION)


@pytest.mark.asyncio
async def test_legacy_oversized_node_is_cut_for_the_request_only():
    query = ("Contract clause text. " * 600) + QUESTION
    legacy = _legacy_node()

    result, captured = await _rerank([_node(), legacy], query, DECLARED)

    assert max(_sent_pair_tokens(captured)) <= WINDOW
    assert ModelTokenizer.shared("bge-m3").count(captured["query_str"]) <= MIN_QUERY_TOKENS
    sent_legacy = next(node for node in captured["nodes"] if node.node.node_id == "legacy")
    assert legacy.content.startswith(sent_legacy.node.get_content())
    assert len(sent_legacy.node.get_content()) < len(legacy.content)
    assert next(node for node in result if node.id == "legacy").content == legacy.content


@pytest.mark.asyncio
async def test_results_keep_the_reranker_order_and_scores():
    result, _ = await _rerank([_node("a"), _node("b")], "notice period", DECLARED)

    assert [node.id for node in result] == ["b", "a"]


def test_short_query_keeps_room_from_the_longest_document():
    budget = ModelTokenBudget.for_model("reranker/bge", DECLARED)
    nodes = [_legacy_node().to_llama_index_node_with_score()]

    request = RerankRequest.fit(QUESTION, nodes, budget)

    tokenizer = ModelTokenizer.shared("bge-m3")
    sent = tokenizer.count(RerankRequest.document_text(request.nodes[0]))
    assert request.query == QUESTION
    assert request.documents_cut == 1
    assert PAIR_OVERHEAD + tokenizer.count(QUESTION) + sent <= WINDOW
