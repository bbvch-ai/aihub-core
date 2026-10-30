from datetime import datetime

import pytest

from swiss_ai_hub.core.persistence.messaging.entities.thread_entity import (
    AgentInstanceRef,
    ThreadEntity,
    User,
)
from swiss_ai_hub.core.persistence.messaging.entities.types.thread_filters import ThreadFilters

pytestmark = pytest.mark.beanie


async def _thread(
    name: str,
    user_id: str = "u1",
    extra_user: str | None = None,
    agent_id: str = "a1",
    agent_class: str = "RAGAgent",
    created_at: datetime | None = None,
) -> ThreadEntity:
    users = [User(user_id=user_id)]
    if extra_user:
        users.append(User(user_id=extra_user))
    entity = ThreadEntity(
        name=name,
        users=users,
        agents=[AgentInstanceRef(agent_id=agent_id, agent_class=agent_class)],
        created_at=created_at or datetime(2026, 1, 1),
    )
    return await entity.insert()


class TestThreadFilteringAndSorting:
    async def test_returns_only_threads_the_user_belongs_to(self):
        await _thread("mine", user_id="u1")
        await _thread("theirs", user_id="u2")
        res = await ThreadEntity.get_paginated_threads_by_user("u1")
        assert [t.name for t in res] == ["mine"]

    async def test_search_is_case_insensitive_substring(self):
        await _thread("Budget Report", user_id="u1")
        await _thread("Vacation Plan", user_id="u1")
        res = await ThreadEntity.get_paginated_threads_by_user("u1", filters=ThreadFilters(search="budget"))
        assert [t.name for t in res] == ["Budget Report"]

    async def test_agent_id_filter(self):
        await _thread("x", user_id="u1", agent_id="rag-1")
        await _thread("y", user_id="u1", agent_id="chat-1")
        res = await ThreadEntity.get_paginated_threads_by_user("u1", filters=ThreadFilters(agent_id="rag-1"))
        assert [t.name for t in res] == ["x"]

    async def test_user_search_id_requires_both_users_present(self):
        await _thread("shared", user_id="u1", extra_user="u2")
        await _thread("solo", user_id="u1")
        res = await ThreadEntity.get_paginated_threads_by_user("u1", filters=ThreadFilters(user_search_id="u2"))
        assert [t.name for t in res] == ["shared"]

    async def test_status_thread_ids_restrict_by_id(self):
        keep = await _thread("keep", user_id="u1")
        await _thread("drop", user_id="u1")
        res = await ThreadEntity.get_paginated_threads_by_user(
            "u1", filters=ThreadFilters(status_thread_ids=[str(keep.id)])
        )
        assert [t.name for t in res] == ["keep"]

    async def test_date_range_filters_created_at_inclusive(self):
        await _thread("old", user_id="u1", created_at=datetime(2026, 1, 1))
        await _thread("mid", user_id="u1", created_at=datetime(2026, 6, 1))
        await _thread("new", user_id="u1", created_at=datetime(2026, 12, 1))
        filters = ThreadFilters(from_date=datetime(2026, 5, 1), to_date=datetime(2026, 7, 1))
        res = await ThreadEntity.get_paginated_threads_by_user("u1", filters=filters)
        assert [t.name for t in res] == ["mid"]

    async def test_default_sort_is_created_at_desc(self):
        await _thread("first", user_id="u1", created_at=datetime(2026, 1, 1))
        await _thread("second", user_id="u1", created_at=datetime(2026, 2, 1))
        res = await ThreadEntity.get_paginated_threads_by_user("u1")
        assert [t.name for t in res] == ["second", "first"]

    async def test_sort_by_name_both_directions(self):
        # lowercase names avoid Mongo's case-sensitive sort surprise (uppercase < lowercase)
        await _thread("banana", user_id="u1")
        await _thread("apple", user_id="u1")
        await _thread("cherry", user_id="u1")
        asc = await ThreadEntity.get_paginated_threads_by_user("u1", sort_by="name", sort_order=1)
        assert [t.name for t in asc] == ["apple", "banana", "cherry"]
        desc = await ThreadEntity.get_paginated_threads_by_user("u1", sort_by="name", sort_order=-1)
        assert [t.name for t in desc] == ["cherry", "banana", "apple"]

    async def test_pagination_skip_and_limit(self):
        for i in range(5):
            await _thread(f"t{i}", user_id="u1", created_at=datetime(2026, 1, 1 + i))
        page = await ThreadEntity.get_paginated_threads_by_user("u1", skip=2, limit=2)
        assert [t.name for t in page] == ["t2", "t1"]

    async def test_combined_filters_narrow_results(self):
        await _thread("Budget", user_id="u1", agent_id="rag-1")
        await _thread("Budget", user_id="u1", agent_id="chat-1")
        filters = ThreadFilters(search="budget", agent_id="rag-1")
        res = await ThreadEntity.get_paginated_threads_by_user("u1", filters=filters)
        assert len(res) == 1
        assert res[0].agents[0].agent_id == "rag-1"


class TestCountThreadsByUser:
    async def test_count_applies_the_same_filters(self):
        await _thread("Budget A", user_id="u1")
        await _thread("Budget B", user_id="u1")
        await _thread("Other", user_id="u1")
        assert await ThreadEntity.count_threads_by_user("u1") == 3
        assert await ThreadEntity.count_threads_by_user("u1", filters=ThreadFilters(search="budget")) == 2


class TestGetOrCreateScheduledThread:
    """One thread per profile rather than per occurrence: a five-minute schedule would otherwise leave
    ~105k single-run threads a year, with nothing cleaning them up."""

    async def test_creates_the_thread_on_first_call(self):
        agent = AgentInstanceRef(agent_class="ImapAgent", agent_id="inbox-1")

        thread = await ThreadEntity.get_or_create_scheduled_thread("Scheduled runs", agent)

        assert thread.name == "Scheduled runs"
        assert thread.users == []
        assert [(a.agent_class, a.agent_id) for a in thread.agents] == [("ImapAgent", "inbox-1")]

    async def test_returns_the_same_thread_on_every_later_call(self):
        agent = AgentInstanceRef(agent_class="ImapAgent", agent_id="inbox-1")

        first = await ThreadEntity.get_or_create_scheduled_thread("Scheduled runs", agent)
        second = await ThreadEntity.get_or_create_scheduled_thread("Scheduled runs", agent)

        assert first.id == second.id
        assert await ThreadEntity.count() == 1

    async def test_does_not_reset_created_at_of_an_existing_thread(self):
        """The thread accumulates a profile's whole run history, so its age must stay its first run's."""
        agent = AgentInstanceRef(agent_class="ImapAgent", agent_id="inbox-1")
        first = await ThreadEntity.get_or_create_scheduled_thread("Scheduled runs", agent)
        # Read back rather than trusting the in-memory instance: Mongo stores milliseconds, so the
        # saved object still carries microseconds the stored document never had.
        stored_created_at = (await ThreadEntity.get_thread_by_id(str(first.id))).created_at

        assert (
            await ThreadEntity.get_or_create_scheduled_thread("Scheduled runs", agent)
        ).created_at == stored_created_at

    async def test_keeps_profiles_apart(self):
        first = AgentInstanceRef(agent_class="ImapAgent", agent_id="inbox-1")
        second = AgentInstanceRef(agent_class="ImapAgent", agent_id="inbox-2")

        await ThreadEntity.get_or_create_scheduled_thread("Scheduled runs", first)
        await ThreadEntity.get_or_create_scheduled_thread("Scheduled runs", second)

        assert await ThreadEntity.count() == 2


class TestUpdateThreadName:
    async def test_update_thread_name_overrides_the_default_name(self):
        thread = await _thread("chat")
        updated = await ThreadEntity.update_thread_name(str(thread.id), "Weather in Ho Chi Minh City")
        assert updated.name == "Weather in Ho Chi Minh City"
        assert (await ThreadEntity.get_thread_by_id(str(thread.id))).name == "Weather in Ho Chi Minh City"
