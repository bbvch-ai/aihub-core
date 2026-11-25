"""Sources carried over from an earlier turn of the chat were released then; with an external access filter they stay
only if the resolver still releases them, so revoking a permission takes effect on the very next turn."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from swiss_ai_hub.core.generative_ai import IngestedNode
from swiss_ai_hub.core.testing.auth_utils import fake_user

from swiss_ai_hub.agent.agents.rag_agent.access.external_access_filters import ExternalAccessFilters
from swiss_ai_hub.agent.agents.rag_agent.configs.external_access_filter_config import ExternalAccessFilterConfig
from swiss_ai_hub.agent.agents.rag_agent.rag_agent import RAGAgent
from swiss_ai_hub.agent.agents.tests.test_task_llm_resolution import _rag_config

CONFIG = ExternalAccessFilterConfig(
    metadata_key="lcdm_knowledge_code", resolver_url="http://resolver/values", api_key="k", cache_ttl_seconds=0
)
RAG_MODULE = "swiss_ai_hub.agent.agents.rag_agent.rag_agent"


@pytest.fixture(autouse=True)
def _fresh_cache() -> None:
    ExternalAccessFilters.forget_answers()


def _node(document_id: str, code: str | list[str] | None) -> IngestedNode:
    return IngestedNode(
        id=f"{document_id}-1",
        content=document_id,
        document_id=document_id,
        source=f"s3://acltest/{document_id}.md",
        namespace="docs",
        document_title=document_id,
        type="content",
        content_type="text",
        created_at="2026-11-25T08:00:00Z",
        updated_at="2026-11-25T08:00:00Z",
        inserted_at="2026-11-25T08:00:00Z",
        score=0.8,
        metadata={},
        record_fields={} if code is None else {"lcdm_knowledge_code": code},
    )


def _released(*values: str) -> httpx.MockTransport:
    return httpx.MockTransport(lambda request: httpx.Response(200, json={"values": list(values)}))


def test_only_carried_nodes_still_released_stay() -> None:
    nodes = [_node("ksb", "KSB/DOK"), _node("vertraulich", "NEST/VERTRAULICH"), _node("ohne-code", None)]

    kept = asyncio.run(ExternalAccessFilters.still_visible(nodes, CONFIG, fake_user(), _released("KSB/DOK")))

    assert [node.document_id for node in kept] == ["ksb"]


def test_a_carried_node_with_several_codes_stays_if_one_is_released() -> None:
    nodes = [_node("geteilt", ["NEST/DOK", "KSB/DOK"])]

    kept = asyncio.run(ExternalAccessFilters.still_visible(nodes, CONFIG, fake_user(), _released("KSB/DOK")))

    assert [node.document_id for node in kept] == ["geteilt"]


def test_a_failing_resolver_drops_every_carried_node() -> None:
    failing = httpx.MockTransport(lambda request: httpx.Response(503))

    kept = asyncio.run(ExternalAccessFilters.still_visible([_node("ksb", "KSB/DOK")], CONFIG, fake_user(), failing))

    assert kept == []


def _combine(config_overrides: dict, carried: list[IngestedNode]) -> MagicMock:
    with (
        patch(f"{RAG_MODULE}.do_read_carried_grounding_nodes", new=AsyncMock(return_value=carried)),
        patch(f"{RAG_MODULE}.do_order_nodes_by_documents", new=AsyncMock(return_value="combined")) as combine,
        patch(
            f"{RAG_MODULE}.ExternalAccessFilters.still_visible", new=AsyncMock(return_value=carried[:1])
        ) as still_visible,
    ):
        asyncio.run(
            RAGAgent().order_nodes_by_documents_step(
                event=MagicMock(),
                t=MagicMock(),
                agent_config=_rag_config(**config_overrides),
                displayer=MagicMock(),
                thread_context=MagicMock(),
                user=fake_user(),
            )
        )
    combine.still_visible = still_visible
    return combine


def test_the_combine_step_checks_carried_nodes_when_the_filter_is_on() -> None:
    carried = [_node("ksb", "KSB/DOK"), _node("vertraulich", "NEST/VERTRAULICH")]

    combine = _combine({"external_access_filter": CONFIG}, carried)

    combine.still_visible.assert_awaited_once()
    assert combine.await_args.kwargs["carried_nodes"] == carried[:1]


def test_without_the_filter_carried_nodes_are_unchanged() -> None:
    carried = [_node("ksb", "KSB/DOK"), _node("vertraulich", "NEST/VERTRAULICH")]

    combine = _combine({}, carried)

    combine.still_visible.assert_not_awaited()
    assert combine.await_args.kwargs["carried_nodes"] == carried
