import hashlib
import re
from datetime import datetime
from typing import Any, Self

from beanie import Document
from beanie.exceptions import DocumentNotFound
from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from swiss_ai_hub.core.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn
from swiss_ai_hub.core.persistence.messaging.entities.types.thread_filters import ThreadFilters
from swiss_ai_hub.core.persistence.messaging.entities.types.thread_sort import SortOrder


class User(BaseModel):
    model_config = ConfigDict(extra="allow")

    user_id: str


class AgentInstanceRef(BaseModel):
    """Reference to an agent instance participating in a thread."""

    model_config = ConfigDict(extra="allow")

    agent_id: str
    agent_class: str


class ThreadEntity(Document):
    """A conversation: the users and agent instances in it, and the process walkthrough it belongs to, if any.

    Unknown fields are kept (`extra="allow"`): the MongoEngine document ran `strict: False`, so stored rows may
    carry fields this model does not declare, and a full rewrite must not drop them. `created_at` stays naive
    local time, as MongoEngine wrote it (see #1971).
    """

    model_config = ConfigDict(extra="allow")

    name: str
    created_at: datetime
    process_class: str | None = None
    process_id: str | None = None
    process_walkthrough_id: str | None = None
    users: list[User] = Field(default_factory=list)
    agents: list[AgentInstanceRef] = Field(default_factory=list)

    class Settings:
        name = "threads"
        keep_nulls = False
        use_state_management = True
        state_management_replace_objects = True
        indexes = [
            IndexModel([("created_at", ASCENDING)]),
            IndexModel([("process_walkthrough_id", ASCENDING)]),
            IndexModel([("agents.agent_id", ASCENDING), ("agents.agent_class", ASCENDING)]),
            IndexModel([("users.user_id", ASCENDING), ("created_at", DESCENDING)]),
            IndexModel([("users.user_id", ASCENDING), ("name", ASCENDING)]),
        ]

    @classmethod
    @trace_fn
    async def create_thread(
        cls, name: str, users: list[User], agents: list[AgentInstanceRef], thread_id: ObjectId | None = None
    ) -> Self:
        thread = cls(id=thread_id or ObjectId(), name=name, users=users, agents=agents, created_at=datetime.now())
        return await thread.insert()

    @classmethod
    @trace_fn
    async def get_or_create_scheduled_thread(cls, name: str, agent: AgentInstanceRef) -> Self:
        """The one thread every scheduled run of a given profile fires into.

        One thread per occurrence would leave a profile running every five minutes with ~105k
        single-run threads a year and nothing to clean them up — invisible today only because the
        threads have no members, and a wall of identical entries in the user's list the moment
        thread membership lands. Many runs in one thread is the ordinary Thread → Display → Run
        model; a chat conversation is exactly that.

        The id is derived from the profile rather than looked up by field, so two replicas racing a
        handover converge on the same document instead of creating a second thread.
        """
        thread_id = cls.scheduled_thread_id(agent)
        existing = await cls.get(thread_id)
        if existing:
            return existing
        return await cls.create_thread(name, users=[], agents=[agent], thread_id=thread_id)

    @staticmethod
    def scheduled_thread_id(agent: AgentInstanceRef) -> ObjectId:
        """The deterministic thread id of a profile's scheduled runs.

        An ObjectId normally encodes its creation time in the leading bytes; this one does not, so read
        a scheduled thread's age from `created_at` and never from its id.
        """
        digest = hashlib.sha256(f"{agent.agent_class}/{agent.agent_id}".encode()).digest()
        return ObjectId(digest[:12])

    @classmethod
    @trace_fn
    async def create_process_thread(
        cls,
        name: str,
        agent: AgentInstanceRef,
        thread_id: ObjectId,
        process_class: str,
        process_id: str,
        process_walkthrough_id: str,
    ) -> Self:
        thread = cls(
            id=thread_id,
            name=name,
            users=[],
            agents=[agent],
            process_class=process_class,
            process_id=process_id,
            process_walkthrough_id=process_walkthrough_id,
            created_at=datetime.now(),
        )
        return await thread.insert()

    @classmethod
    @trace_fn
    async def get_thread_by_id(cls, thread_id: str) -> Self:
        """The thread with `thread_id`; raises `DocumentNotFound` when there is none."""
        thread = await cls.get(ObjectId(thread_id))
        if thread is None:
            raise DocumentNotFound(f"Thread {thread_id} not found")
        return thread

    @classmethod
    @trace_fn
    async def get_threads_by_user(cls, user_id: str) -> list[Self]:
        return await cls.find({"users.user_id": user_id}).to_list()

    @staticmethod
    def _filter_criteria(filters: ThreadFilters | None) -> dict[str, Any]:
        if not filters:
            return {}
        criteria: dict[str, Any] = {}
        if filters.search:
            criteria["name"] = {"$regex": re.escape(filters.search), "$options": "i"}
        if filters.agent_id:
            criteria["agents.agent_id"] = filters.agent_id
        if filters.user_search_id:
            criteria["$and"] = [{"users.user_id": filters.user_search_id}]
        if filters.status_thread_ids is not None:
            criteria["_id"] = {"$in": [ObjectId(thread_id) for thread_id in filters.status_thread_ids]}
        created_at: dict[str, datetime] = {}
        if filters.from_date is not None:
            created_at["$gte"] = filters.from_date
        if filters.to_date is not None:
            created_at["$lte"] = filters.to_date
        if created_at:
            criteria["created_at"] = created_at
        return criteria

    @classmethod
    @trace_fn
    async def count_threads_by_user(cls, user_id: str, filters: ThreadFilters | None = None) -> int:
        """Count the total number of threads that include the specified user."""
        return await cls.find({"users.user_id": user_id, **cls._filter_criteria(filters)}).count()

    @classmethod
    @trace_fn
    async def count_threads_by_agent(cls, agent_class: str, agent_id: str) -> int:
        """Count the total number of threads that include the specified agent."""
        return await cls.find(cls._agent_criteria(agent_class, agent_id)).count()

    @classmethod
    @trace_fn
    async def get_paginated_threads_by_user(
        cls,
        user_id: str,
        skip: int = 0,
        limit: int = 20,
        sort_by: str = "created_at",
        sort_order: SortOrder = SortOrder.DESCENDING,
        filters: ThreadFilters | None = None,
    ) -> list[Self]:
        """Get a paginated list of threads that include the specified user."""
        query = cls.find({"users.user_id": user_id, **cls._filter_criteria(filters)})
        return await query.sort(cls.get_order_by(sort_by, sort_order)).skip(skip).limit(limit).to_list()

    @staticmethod
    def get_order_by(sort_by: str, sort_order: int) -> str:
        field_mapping = {
            "created_at": "created_at",
            "name": "name",
        }

        if sort_by in field_mapping:
            prefix = "-" if sort_order == -1 else ""
            return f"{prefix}{field_mapping[sort_by]}"
        return "-created_at"

    @staticmethod
    def _agent_criteria(agent_class: str, agent_id: str) -> dict[str, Any]:
        """Matches what MongoEngine's `agents__agent_id=..., agents__agent_class=...` did: each on any member."""
        return {"agents.agent_id": agent_id, "agents.agent_class": agent_class}

    @classmethod
    @trace_fn
    async def get_paginated_threads_by_agent(
        cls, agent_class: str, agent_id: str, user_id: str | None = None, skip: int = 0, limit: int = 20
    ) -> list[Self]:
        """
        Get a paginated list of threads that include the specified agent.
        If a user_id is provided, it also filters for threads containing that user.
        """
        criteria = cls._agent_criteria(agent_class, agent_id)
        if user_id:
            criteria["users.user_id"] = user_id
        return await cls.find(criteria).sort("-created_at").skip(skip).limit(limit).to_list()

    @classmethod
    @trace_fn
    async def get_threads_by_users(cls, user_ids: list[str]) -> list[Self]:
        return await cls.find({"users.user_id": {"$in": user_ids}}).to_list()

    @classmethod
    @trace_fn
    async def get_threads_by_agent(cls, agent_class: str, agent_id: str) -> list[Self]:
        return await cls.find(cls._agent_criteria(agent_class, agent_id)).to_list()

    @classmethod
    @trace_fn
    async def get_thread_ids_for_user(cls, user_id: str) -> list[str]:
        collection = cls.get_pymongo_collection()
        return [str(row["_id"]) async for row in collection.find({"users.user_id": user_id}, {"_id": 1})]

    @classmethod
    @trace_fn
    async def update_thread_name(cls, thread_id: str, name: str) -> Self:
        thread = await cls.get_thread_by_id(thread_id)
        thread.name = name
        await thread.save_changes()
        return thread

    @classmethod
    @trace_fn
    async def add_user_to_thread(cls, thread_id: str, user: User) -> Self:
        thread = await cls.get_thread_by_id(thread_id)
        thread.users.append(user)
        await thread.save_changes()
        return thread

    @classmethod
    @trace_fn
    async def add_agent_to_thread(cls, thread_id: str, agent: AgentInstanceRef) -> Self:
        thread = await cls.get_thread_by_id(thread_id)
        thread.agents.append(agent)
        await thread.save_changes()
        return thread

    @classmethod
    @trace_fn
    async def remove_user_from_thread(cls, thread_id: str, user_id: str) -> Self:
        thread = await cls.get_thread_by_id(thread_id)
        thread.users = [user for user in thread.users if user.user_id != user_id]
        await thread.save_changes()
        return thread

    @classmethod
    @trace_fn
    async def remove_agent_from_thread(cls, thread_id: str, agent_class: str, agent_id: str) -> Self:
        thread = await cls.get_thread_by_id(thread_id)
        thread.agents = [
            agent for agent in thread.agents if agent.agent_id != agent_id and agent.agent_class != agent_class
        ]
        await thread.save_changes()
        return thread

    @trace_fn
    async def claim_for_process(self, process_class: str, process_id: str, process_walkthrough_id: str) -> Self:
        self.process_class = process_class
        self.process_id = process_id
        self.process_walkthrough_id = process_walkthrough_id
        await self.save_changes()
        return self

    @classmethod
    @trace_fn
    async def delete_thread(cls, thread_id: str) -> Self:
        thread = await cls.get_thread_by_id(thread_id)
        await thread.delete()
        return thread
