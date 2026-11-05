import asyncio
from collections.abc import Iterator
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from beanie.exceptions import DocumentNotFound
from bson import ObjectId
from swiss_ai_hub.core.persistence.messaging.entities.thread_entity import ThreadEntity

from swiss_ai_hub.api.sockets.sender import web_socket_sender
from swiss_ai_hub.api.sockets.sender.web_socket_sender import WebSocketSender

THREAD_ID = str(ObjectId())


class _CountingThreadLookup:
    """Stands in for the database lookup: answers after a delay, so a burst of events overlaps as it does live."""

    def __init__(self, user_ids: list[str] | None) -> None:
        self.user_ids = user_ids
        self.calls = 0

    async def __call__(self, thread_id: str) -> SimpleNamespace:
        self.calls += 1
        await asyncio.sleep(0.02)
        if self.user_ids is None:
            raise DocumentNotFound(f"Thread {thread_id} not found")
        return SimpleNamespace(users=[SimpleNamespace(user_id=user_id) for user_id in self.user_ids])


@pytest.fixture
def empty_cache() -> Iterator[None]:
    web_socket_sender._USERS_IN_THREAD_CACHE.clear()
    yield
    web_socket_sender._USERS_IN_THREAD_CACHE.clear()


@pytest.mark.asyncio
async def test_a_burst_of_events_for_one_thread_shares_one_lookup(empty_cache: None) -> None:
    """Each display event is handled in its own task; the opening burst of a run must not read the thread per event."""
    lookup = _CountingThreadLookup(["alice", "bob"])

    with patch.object(ThreadEntity, "get_thread_by_id", new=lookup):
        results = await asyncio.gather(*(WebSocketSender.get_users_in_thread(THREAD_ID) for _ in range(28)))

    assert lookup.calls == 1
    assert all(result == ["alice", "bob"] for result in results)


@pytest.mark.asyncio
async def test_a_missing_thread_fails_every_waiting_event_and_is_retried_later(empty_cache: None) -> None:
    lookup = _CountingThreadLookup(None)

    with patch.object(ThreadEntity, "get_thread_by_id", new=lookup):
        results = await asyncio.gather(
            *(WebSocketSender.get_users_in_thread(THREAD_ID) for _ in range(5)), return_exceptions=True
        )
        assert all(isinstance(result, DocumentNotFound) for result in results)
        assert lookup.calls == 1

        lookup.user_ids = ["alice"]
        assert await WebSocketSender.get_users_in_thread(THREAD_ID) == ["alice"]

    assert lookup.calls == 2


@pytest.mark.asyncio
async def test_a_cancelled_event_does_not_cancel_the_shared_lookup(empty_cache: None) -> None:
    lookup = _CountingThreadLookup(["alice"])

    with patch.object(ThreadEntity, "get_thread_by_id", new=lookup):
        first = asyncio.create_task(WebSocketSender.get_users_in_thread(THREAD_ID))
        await asyncio.sleep(0)
        others = [asyncio.create_task(WebSocketSender.get_users_in_thread(THREAD_ID)) for _ in range(3)]
        await asyncio.sleep(0)
        first.cancel()
        results = await asyncio.gather(*others)

    assert first.cancelled()
    assert lookup.calls == 1
    assert all(result == ["alice"] for result in results)
