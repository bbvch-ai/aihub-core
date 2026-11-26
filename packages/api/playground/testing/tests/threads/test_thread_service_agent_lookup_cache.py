import asyncio
from collections.abc import Iterator
from unittest.mock import patch

import pytest
from fastapi import HTTPException

from swiss_ai_hub.api.i18n.api_locale_handler import ApiLocaleHandler
from swiss_ai_hub.api.routes.agent.agent_service import AgentService
from swiss_ai_hub.api.routes.thread import thread_service
from swiss_ai_hub.api.routes.thread.thread_service import ThreadService


class _CountingAgentLookup:
    """Stands in for the database lookup: answers after a delay, so concurrent callers overlap as they do live."""

    def __init__(self, answers: dict[tuple[str, str], object | Exception]) -> None:
        self.answers = answers
        self.calls: list[tuple[str, str]] = []

    async def __call__(self, agent_class: str, agent_id: str, t: ApiLocaleHandler) -> object:
        self.calls.append((agent_class, agent_id))
        await asyncio.sleep(0.02)
        answer = self.answers[(agent_class, agent_id)]
        if isinstance(answer, Exception):
            raise answer
        return answer


@pytest.fixture
def empty_cache() -> Iterator[None]:
    thread_service._MINIMAL_AGENT_DTO_CACHE.clear()
    yield
    thread_service._MINIMAL_AGENT_DTO_CACHE.clear()


@pytest.mark.asyncio
async def test_threads_sharing_an_agent_share_one_lookup(empty_cache: None) -> None:
    """The threads of a page are built concurrently; ten of them naming one agent must cost one lookup, not ten."""
    agent = object()
    lookup = _CountingAgentLookup({("RAGAgent", "hr"): agent})
    t = ApiLocaleHandler(locale="en")

    with patch.object(AgentService, "get_minimal_agent_instance", new=lookup):
        results = await asyncio.gather(
            *(ThreadService._fetch_minimal_agent_dto("RAGAgent", "hr", t) for _ in range(10))
        )

    assert lookup.calls == [("RAGAgent", "hr")]
    assert all(result is agent for result in results)


@pytest.mark.asyncio
async def test_each_distinct_agent_is_looked_up_once(empty_cache: None) -> None:
    answers = {
        ("RAGAgent", "hr"): object(),
        ("LLMWrappingAgent", "minutes"): object(),
        ("ReleaseNotesAgent", "demo"): object(),
    }
    lookup = _CountingAgentLookup(answers)
    t = ApiLocaleHandler(locale="en")
    page = [*[("RAGAgent", "hr")] * 5, *[("LLMWrappingAgent", "minutes")] * 3, *[("ReleaseNotesAgent", "demo")] * 2]

    with patch.object(AgentService, "get_minimal_agent_instance", new=lookup):
        results = await asyncio.gather(*(ThreadService._fetch_minimal_agent_dto(c, i, t) for c, i in page))

    assert sorted(lookup.calls) == sorted(answers)
    assert results == [answers[ref] for ref in page]


@pytest.mark.asyncio
async def test_a_cancelled_caller_does_not_cancel_the_shared_lookup(empty_cache: None) -> None:
    """The first caller starts the lookup; it being cancelled (a client went away) must not fail the others."""
    agent = object()
    lookup = _CountingAgentLookup({("RAGAgent", "hr"): agent})
    t = ApiLocaleHandler(locale="en")

    with patch.object(AgentService, "get_minimal_agent_instance", new=lookup):
        first = asyncio.create_task(ThreadService._fetch_minimal_agent_dto("RAGAgent", "hr", t))
        await asyncio.sleep(0)
        others = [asyncio.create_task(ThreadService._fetch_minimal_agent_dto("RAGAgent", "hr", t)) for _ in range(3)]
        await asyncio.sleep(0)
        first.cancel()
        results = await asyncio.gather(*others)

    assert first.cancelled()
    assert lookup.calls == [("RAGAgent", "hr")]
    assert all(result is agent for result in results)


@pytest.mark.asyncio
async def test_a_missing_agent_is_remembered_like_a_found_one(empty_cache: None) -> None:
    """A deleted profile resolves to None; that answer is cached too, so a page does not log its failure per thread."""
    lookup = _CountingAgentLookup({("RAGAgent", "deleted"): HTTPException(status_code=404, detail="not found")})
    t = ApiLocaleHandler(locale="en")

    with patch.object(AgentService, "get_minimal_agent_instance", new=lookup):
        first = await ThreadService._fetch_minimal_agent_dto("RAGAgent", "deleted", t)
        second = await ThreadService._fetch_minimal_agent_dto("RAGAgent", "deleted", t)

    assert first is None and second is None
    assert lookup.calls == [("RAGAgent", "deleted")]
