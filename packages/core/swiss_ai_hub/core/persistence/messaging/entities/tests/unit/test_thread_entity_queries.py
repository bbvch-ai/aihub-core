from datetime import datetime

import pytest
from mongoengine import connect, disconnect

from swiss_ai_hub.core.infrastructure.api.ai_hub_settings import AIHubSettings
from swiss_ai_hub.core.infrastructure.mongo.mongo_settings import MongoSettings
from swiss_ai_hub.core.persistence.messaging.entities.thread_entity import (
    AgentInstanceRef,
    ThreadEntity,
    User,
)
from swiss_ai_hub.core.persistence.messaging.entities.types.thread_filters import ThreadFilters


@pytest.fixture
def mongo_connection():
    connect(
        db=AIHubSettings().MONGO_MAIN_DB_NAME,
        host=MongoSettings().CONNECTION_STRING.get_secret_value(),
    )
    yield
    disconnect()


@pytest.fixture(autouse=True)
def clean_threads(mongo_connection):
    ThreadEntity.objects.delete()
    yield
    ThreadEntity.objects.delete()


def _thread(
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
    entity.save()
    return entity


class TestThreadFilteringAndSorting:
    def test_returns_only_threads_the_user_belongs_to(self):
        _thread("mine", user_id="u1")
        _thread("theirs", user_id="u2")
        res = ThreadEntity.get_paginated_threads_by_user("u1")
        assert [t.name for t in res] == ["mine"]

    def test_search_is_case_insensitive_substring(self):
        _thread("Budget Report", user_id="u1")
        _thread("Vacation Plan", user_id="u1")
        res = ThreadEntity.get_paginated_threads_by_user("u1", filters=ThreadFilters(search="budget"))
        assert [t.name for t in res] == ["Budget Report"]

    def test_agent_id_filter(self):
        _thread("x", user_id="u1", agent_id="rag-1")
        _thread("y", user_id="u1", agent_id="chat-1")
        res = ThreadEntity.get_paginated_threads_by_user("u1", filters=ThreadFilters(agent_id="rag-1"))
        assert [t.name for t in res] == ["x"]

    def test_user_search_id_requires_both_users_present(self):
        _thread("shared", user_id="u1", extra_user="u2")
        _thread("solo", user_id="u1")
        res = ThreadEntity.get_paginated_threads_by_user("u1", filters=ThreadFilters(user_search_id="u2"))
        assert [t.name for t in res] == ["shared"]

    def test_status_thread_ids_restrict_by_id(self):
        keep = _thread("keep", user_id="u1")
        _thread("drop", user_id="u1")
        res = ThreadEntity.get_paginated_threads_by_user("u1", filters=ThreadFilters(status_thread_ids=[str(keep.id)]))
        assert [t.name for t in res] == ["keep"]

    def test_date_range_filters_created_at_inclusive(self):
        _thread("old", user_id="u1", created_at=datetime(2026, 1, 1))
        _thread("mid", user_id="u1", created_at=datetime(2026, 6, 1))
        _thread("new", user_id="u1", created_at=datetime(2026, 12, 1))
        filters = ThreadFilters(from_date=datetime(2026, 5, 1), to_date=datetime(2026, 7, 1))
        res = ThreadEntity.get_paginated_threads_by_user("u1", filters=filters)
        assert [t.name for t in res] == ["mid"]

    def test_default_sort_is_created_at_desc(self):
        _thread("first", user_id="u1", created_at=datetime(2026, 1, 1))
        _thread("second", user_id="u1", created_at=datetime(2026, 2, 1))
        res = ThreadEntity.get_paginated_threads_by_user("u1")
        assert [t.name for t in res] == ["second", "first"]

    def test_sort_by_name_both_directions(self):
        # lowercase names avoid Mongo's case-sensitive sort surprise (uppercase < lowercase)
        _thread("banana", user_id="u1")
        _thread("apple", user_id="u1")
        _thread("cherry", user_id="u1")
        asc = ThreadEntity.get_paginated_threads_by_user("u1", sort_by="name", sort_order=1)
        assert [t.name for t in asc] == ["apple", "banana", "cherry"]
        desc = ThreadEntity.get_paginated_threads_by_user("u1", sort_by="name", sort_order=-1)
        assert [t.name for t in desc] == ["cherry", "banana", "apple"]

    def test_pagination_skip_and_limit(self):
        for i in range(5):
            _thread(f"t{i}", user_id="u1", created_at=datetime(2026, 1, 1 + i))
        page = ThreadEntity.get_paginated_threads_by_user("u1", skip=2, limit=2)
        assert [t.name for t in page] == ["t2", "t1"]

    def test_combined_filters_narrow_results(self):
        _thread("Budget", user_id="u1", agent_id="rag-1")
        _thread("Budget", user_id="u1", agent_id="chat-1")
        filters = ThreadFilters(search="budget", agent_id="rag-1")
        res = list(ThreadEntity.get_paginated_threads_by_user("u1", filters=filters))
        assert len(res) == 1
        assert res[0].agents[0].agent_id == "rag-1"


class TestCountThreadsByUser:
    def test_count_applies_the_same_filters(self):
        _thread("Budget A", user_id="u1")
        _thread("Budget B", user_id="u1")
        _thread("Other", user_id="u1")
        assert ThreadEntity.count_threads_by_user("u1") == 3
        assert ThreadEntity.count_threads_by_user("u1", filters=ThreadFilters(search="budget")) == 2


class TestUpdateThreadName:
    def test_update_thread_name_overrides_the_default_name(self):
        thread = _thread("chat")
        updated = ThreadEntity.update_thread_name(str(thread.id), "Weather in Ho Chi Minh City")
        assert updated.name == "Weather in Ho Chi Minh City"
        assert ThreadEntity.get_thread_by_id(str(thread.id)).name == "Weather in Ho Chi Minh City"
