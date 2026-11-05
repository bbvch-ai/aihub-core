"""A RAG turn whose reranker fails answers from the retrieval order instead of failing the run.

The reranker is bounded at 30 s (aihub-core-private#349), so a stuck rerank now raises where it used to block for five
minutes; the turn keeps the best-scored retrieved nodes, as the knowledge capability does, and says on the event that
they were not reranked.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from swiss_ai_hub.core.generative_ai import IngestedNode, RerankingModelConfig

from swiss_ai_hub.agent.agents.rag_agent.configs.reranking_config import RerankingConfig
from swiss_ai_hub.agent.rag.step_functions import do_rerank_nodes

MODULE = "swiss_ai_hub.agent.rag.step_functions"


def _node(document_id: str, score: float) -> IngestedNode:
    return IngestedNode(
        id=f"{document_id}-{score}",
        content=document_id,
        document_id=document_id,
        source=f"s3://handbook/{document_id}.md",
        namespace="handbook",
        document_title=document_id.title(),
        type="content",
        content_type="text",
        created_at="2023-11-14T22:13:20Z",
        updated_at="2023-11-14T22:13:20Z",
        inserted_at="2023-11-14T22:13:20Z",
        score=score,
    )


NODES = [_node("low", 0.2), _node("high", 0.9), _node("middle", 0.5)]
CONFIG = RerankingConfig(reranking_model=RerankingModelConfig(model_name="reranker/bge", top_n=2))


async def _rerank(rerank_nodes: AsyncMock):
    with patch(f"{MODULE}.rerank_nodes", new=rerank_nodes):
        return await do_rerank_nodes(NODES, "query", CONFIG, AsyncMock(), MagicMock(), None)


@pytest.mark.asyncio
async def test_a_failing_reranker_keeps_the_best_scored_nodes():
    event = await _rerank(AsyncMock(side_effect=TimeoutError("rerank timed out")))

    assert [node.document_id for node in event.output_nodes] == ["high", "middle"]
    assert event.reranked is False
    assert event.input_nodes == NODES


@pytest.mark.asyncio
async def test_a_working_reranker_keeps_its_order():
    reranked = [NODES[0], NODES[2]]

    event = await _rerank(AsyncMock(return_value=reranked))

    assert event.output_nodes == reranked
    assert event.reranked is True
