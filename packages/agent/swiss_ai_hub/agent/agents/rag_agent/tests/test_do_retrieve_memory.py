"""Memory retrieval degrades instead of taking the run down, and passes the scope it was asked for (#1713).

A raising retrieval step ends the run with an `ExceptionEvent`, but marking the step `stop_on_error=False`
is worse: the dispatcher then publishes nothing, and `check_memory_ready_for_chat_history` blocks until the
retrieval event exists — so the run hangs rather than degrading. The contract pinned here is that failure,
timeout included, yields an *empty* event, which keeps that precondition satisfiable.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest
from swiss_ai_hub.core.events.agent import (
    RAGStartEvent,
    RetrieveOrganizationMemoryEvent,
    RetrieveUserMemoryEvent,
)
from swiss_ai_hub.core.generative_ai import OrgMemoryReadConfig
from swiss_ai_hub.core.infrastructure.mem0.types.memory_search_result import MemorySearchResult

from swiss_ai_hub.agent.rag import step_functions
from swiss_ai_hub.agent.rag.preconditions import check_memory_ready_for_chat_history
from swiss_ai_hub.agent.rag.step_functions import do_retrieve_organization_memory, do_retrieve_user_memory


def _event() -> MagicMock:
    event = MagicMock()
    event.user_query = "what is the vacation policy?"
    event.user.id = "user-1"
    return event


def _org_config(**overrides) -> OrgMemoryReadConfig:
    return OrgMemoryReadConfig(
        **{
            "tenant_id": "tenant-1",
            "default_tenant_namespace": None,
            "allowed_tenant_namespaces": [],
            **overrides,
        }
    )


def _failing_memory() -> MagicMock:
    memory = MagicMock()
    memory.search_user_memory = AsyncMock(side_effect=RuntimeError("neo4j unreachable"))
    memory.search_organization_memory = AsyncMock(side_effect=RuntimeError("neo4j unreachable"))
    return memory


def _empty_result_memory() -> MagicMock:
    memory = MagicMock()
    memory.search_user_memory = AsyncMock(return_value=MemorySearchResult(results=[]))
    memory.search_organization_memory = AsyncMock(return_value=MemorySearchResult(results=[]))
    return memory


@pytest.mark.asyncio
async def test_user_memory_failure_yields_empty_event():
    result = await do_retrieve_user_memory(event=_event(), memory=_failing_memory(), rerank=True)

    assert isinstance(result, RetrieveUserMemoryEvent)
    assert result.memories == []
    assert result.relations == []


@pytest.mark.asyncio
async def test_organization_memory_failure_yields_empty_event():
    result = await do_retrieve_organization_memory(event=_event(), org_memory=_org_config(), memory=_failing_memory())

    assert isinstance(result, RetrieveOrganizationMemoryEvent)
    assert result.memories == []
    assert result.relations == []


@pytest.mark.asyncio
async def test_hung_backend_degrades_rather_than_stalling_the_turn(monkeypatch):
    """A stall blocks the chat turn as surely as a raise ends it, so the timeout takes the same path."""
    monkeypatch.setattr(step_functions, "MEMORY_RETRIEVAL_TIMEOUT_SECONDS", 0.01)

    async def _never_returns(**_kwargs):
        await asyncio.sleep(30)

    memory = MagicMock()
    memory.search_organization_memory = _never_returns

    result = await do_retrieve_organization_memory(event=_event(), org_memory=_org_config(), memory=memory)

    assert result.memories == []


@pytest.mark.asyncio
async def test_degraded_events_still_satisfy_the_chat_history_precondition():
    """The point of returning an empty event rather than nothing: the run must continue to the answer."""
    config = MagicMock()
    config.user_memory.enable_user_memory_retrieval = True
    config.org_memory = _org_config()

    user_event = await do_retrieve_user_memory(event=_event(), memory=_failing_memory(), rerank=True)
    org_event = await do_retrieve_organization_memory(
        event=_event(), org_memory=_org_config(), memory=_failing_memory()
    )

    assert check_memory_ready_for_chat_history(config, True, user_event, org_event) is True


@pytest.mark.asyncio
async def test_user_memory_search_receives_the_query_and_rerank_flag():
    memory = _empty_result_memory()

    await do_retrieve_user_memory(event=_event(), memory=memory, rerank=False)

    kwargs = memory.search_user_memory.await_args.kwargs
    assert kwargs["query"] == "what is the vacation policy?"
    assert kwargs["user_id"] == "user-1"
    assert kwargs["rerank"] is False


@pytest.mark.asyncio
async def test_organization_memory_search_receives_the_resolved_scope():
    memory = _empty_result_memory()
    org_memory = _org_config(
        default_tenant_namespace="engineering",
        allowed_tenant_namespaces=["engineering", "legal"],
        rerank_organization_memory=False,
    )

    await do_retrieve_organization_memory(event=_event(), org_memory=org_memory, memory=memory)

    kwargs = memory.search_organization_memory.await_args.kwargs
    assert kwargs["tenant_id"] == "tenant-1"
    assert kwargs["tenant_namespaces"] == ["engineering", "legal"]
    assert kwargs["user_id"] is None
    assert kwargs["rerank"] is False


@pytest.mark.asyncio
async def test_namespace_outside_the_allow_list_stays_fatal():
    """Namespace validation is a caller error, deliberately outside the degrade-to-empty safety net."""
    event = MagicMock(spec=RAGStartEvent)
    event.user_query = "q"
    event.org_memory_namespaces = ["enginering"]
    org_memory = _org_config(default_tenant_namespace="engineering", allowed_tenant_namespaces=["engineering"])

    memory = _empty_result_memory()

    with pytest.raises(ValueError, match="not in the configured allow-list"):
        await do_retrieve_organization_memory(event=event, org_memory=org_memory, memory=memory)
