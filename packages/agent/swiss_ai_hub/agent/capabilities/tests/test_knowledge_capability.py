"""The knowledge capability's contract: `search` always answers, searches only the referenced collections the asking
user may read, and names the others in the block so the answer can say it could not use them.

A turn without references answers with an empty block so a waiting step never hangs.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from swiss_ai_hub.core.events.agent import KnowledgeReference, KnowledgeSearchedEvent
from swiss_ai_hub.core.generative_ai import IngestedNode
from swiss_ai_hub.core.i18n.locale_handler import LocaleHandler

from swiss_ai_hub.agent.agents.llm_wrapping_agent.llm_wrapping_agent import LLMWrappingAgent
from swiss_ai_hub.agent.capabilities.knowledge.knowledge import Knowledge
from swiss_ai_hub.agent.capabilities.knowledge.knowledge_fields import KnowledgeFields

MODULE = "swiss_ai_hub.agent.capabilities.knowledge.knowledge"
POLICIES = KnowledgeReference(database="sftplive", namespace="policies")
REPORTS = KnowledgeReference(database="sftplive", namespace="reports")


def _node(text: str, document_id: str, score: float) -> IngestedNode:
    return IngestedNode(
        id=f"{document_id}-{score}",
        content=text,
        document_id=document_id,
        source=f"s3://sftplive/{document_id}.md",
        namespace="policies",
        document_title=document_id.title(),
        type="content",
        content_type="text",
        created_at="2023-11-14T22:13:20Z",
        updated_at="2023-11-14T22:13:20Z",
        inserted_at="2023-11-14T22:13:20Z",
        score=score,
    )


def _access(readable: set[str]) -> MagicMock:
    access = MagicMock()
    access.has_access_to_knowledge_namespace.side_effect = lambda _database, namespace: namespace in readable
    return access


async def _search(
    references: list[KnowledgeReference],
    access: MagicMock | None,
    nodes: list[IngestedNode],
    reranked: list[IngestedNode] | Exception | None = None,
    cite_sources: bool = True,
) -> tuple[KnowledgeSearchedEvent, AsyncMock]:
    rerank = AsyncMock(side_effect=reranked) if isinstance(reranked, Exception) else AsyncMock(return_value=reranked)
    with (
        patch(f"{MODULE}.UserScopedRetrievers.namespaces_of", return_value=["policies", "reports"]),
        patch(f"{MODULE}.ReferencedKnowledge.retrievers", return_value=["retriever"]),
        patch(f"{MODULE}.retrieve_from_all_sources", new=AsyncMock(return_value=nodes)) as retrieve,
        patch(f"{MODULE}.rerank_nodes", new=rerank),
        patch(
            f"{MODULE}.KnowledgeCollectionLabel.of_reference",
            side_effect=lambda reference, _locale: f"SFTP Live / {reference.namespace.title()}",
        ),
    ):
        event = await Knowledge.search_step(
            LLMWrappingAgent(),
            request=Knowledge.search(references, "How many vacation days?", cite_sources),
            knowledge=KnowledgeFields(),
            t=LocaleHandler("en"),
            user=None,
            access=access,
        )
    return event, retrieve


@pytest.mark.asyncio
async def test_no_reference_answers_empty_without_searching():
    event, retrieve = await _search([], _access({"policies"}), [])

    assert (event.block, event.grounding_nodes, event.refused) == ([], [], [])
    retrieve.assert_not_awaited()


@pytest.mark.asyncio
async def test_a_readable_collection_is_searched_and_cited():
    handbook = _node("25 vacation days per year.", "handbook", 0.9)

    event, retrieve = await _search([POLICIES], _access({"policies"}), [handbook], reranked=[handbook])

    retrieve.assert_awaited_once()
    assert event.grounding_nodes == [handbook]
    assert event.refused == []
    assert f"id='{handbook.citation_id}'" in event.block[0].content
    assert "25 vacation days per year." in event.block[0].content
    assert "Cite the documents" in event.block[1].content


@pytest.mark.asyncio
async def test_citations_off_leaves_out_the_instruction():
    handbook = _node("25 vacation days per year.", "handbook", 0.9)

    event, _ = await _search([POLICIES], _access({"policies"}), [handbook], reranked=[handbook], cite_sources=False)

    assert len(event.block) == 1


@pytest.mark.asyncio
async def test_a_collection_the_user_may_not_read_is_named_and_not_searched():
    event, retrieve = await _search([REPORTS], _access({"policies"}), [])

    retrieve.assert_not_awaited()
    assert event.refused == [REPORTS]
    assert event.grounding_nodes == []
    assert '"SFTP Live / Reports"' in event.block[0].content
    assert "not available to the user" in event.block[0].content


@pytest.mark.asyncio
async def test_a_mixed_reference_searches_the_readable_part_and_refuses_the_rest():
    handbook = _node("25 vacation days per year.", "handbook", 0.9)

    event, _ = await _search([POLICIES, REPORTS], _access({"policies"}), [handbook], reranked=[handbook])

    assert event.grounding_nodes == [handbook]
    assert event.refused == [REPORTS]
    assert '"SFTP Live / Reports"' in event.block[-1].content


@pytest.mark.asyncio
async def test_a_failing_reranker_keeps_the_best_scored_sections():
    low, high = _node("low", "a", 0.1), _node("high", "b", 0.8)

    event, _ = await _search([POLICIES], _access({"policies"}), [low, high], reranked=RuntimeError("down"))

    assert event.grounding_nodes == [high, low]


@pytest.mark.asyncio
async def test_nothing_found_tells_the_model_so():
    event, _ = await _search([POLICIES], _access({"policies"}), [])

    assert event.grounding_nodes == []
    assert "Nothing in the searched" in event.block[0].content
