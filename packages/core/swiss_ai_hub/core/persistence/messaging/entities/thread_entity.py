from datetime import datetime
from typing import Self

from bson import ObjectId
from mongoengine import DateTimeField, Document, EmbeddedDocument, EmbeddedDocumentField, ListField, StringField

from swiss_ai_hub.core.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn
from swiss_ai_hub.core.persistence.messaging.entities.types.thread_filters import ThreadFilters


class User(EmbeddedDocument):
    user_id = StringField(required=True)


class AgentInstanceRef(EmbeddedDocument):
    """Reference to an agent instance participating in a thread."""

    agent_id = StringField(required=True)
    agent_class = StringField(required=True)


class ThreadEntity(Document):
    meta = {
        "collection": "threads",
        "strict": False,
        "indexes": [
            {"fields": ["users.user_id"]},
            {"fields": ["created_at"]},
            {"fields": ["process_walkthrough_id"]},
            {"fields": ["agents.agent_id", "agents.agent_class"]},
            {"fields": ["users.user_id", "-created_at"]},
        ],
    }
    name = StringField(required=True)
    created_at = DateTimeField(required=True)
    process_class = StringField(required=False)
    process_id = StringField(required=False)
    process_walkthrough_id = StringField(required=False)
    users = ListField(EmbeddedDocumentField(User))
    agents = ListField(EmbeddedDocumentField(AgentInstanceRef))

    @classmethod
    @trace_fn
    def create_thread(
        cls, name: str, users: list[User], agents: list[AgentInstanceRef], thread_id: ObjectId | None = None
    ) -> Self:
        thread = cls(id=thread_id or ObjectId(), name=name, users=users, agents=agents, created_at=datetime.now())
        thread.save()
        return thread

    @classmethod
    @trace_fn
    def create_process_thread(
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
        thread.save()
        return thread

    @classmethod
    @trace_fn
    def get_thread_by_id(cls, thread_id: str) -> Self:
        return cls.objects().get(id=ObjectId(thread_id))

    @classmethod
    @trace_fn
    def get_threads_by_user(cls, user_id: str) -> list["ThreadEntity"]:
        return cls.objects().filter(users__user_id=user_id)

    @staticmethod
    def _apply_filters(query, filters: ThreadFilters | None):
        if not filters:
            return query
        if filters.search:
            query = query.filter(name__icontains=filters.search)
        if filters.agent_id:
            query = query.filter(agents__agent_id=filters.agent_id)
        if filters.user_search_id:
            query = query.filter(users__user_id=filters.user_search_id)
        if filters.status_thread_ids is not None:
            query = query.filter(id__in=filters.status_thread_ids)
        if filters.from_date is not None:
            query = query.filter(created_at__gte=filters.from_date)
        if filters.to_date is not None:
            query = query.filter(created_at__lte=filters.to_date)
        return query

    @classmethod
    @trace_fn
    def count_threads_by_user(cls, user_id: str, filters: ThreadFilters | None = None) -> int:
        """Count the total number of threads that include the specified user."""
        query = cls.objects().filter(users__user_id=user_id)
        query = cls._apply_filters(query, filters)
        return query.count()

    @classmethod
    @trace_fn
    def count_threads_by_agent(cls, agent_class: str, agent_id: str) -> int:
        """Count the total number of threads that include the specified agent."""
        return cls.objects().filter(agents__agent_id=agent_id, agents__agent_class=agent_class).count()

    @classmethod
    @trace_fn
    def get_paginated_threads_by_user(
        cls,
        user_id: str,
        skip: int = 0,
        limit: int = 20,
        sort_by: str = "created_at",
        sort_order: int = -1,
        filters: ThreadFilters | None = None,
    ) -> list["ThreadEntity"]:
        """Get a paginated list of threads that include the specified user."""
        order_by = cls.get_order_by(sort_by, sort_order)
        query = cls.objects().filter(users__user_id=user_id)
        query = cls._apply_filters(query, filters)
        return query.order_by(order_by).skip(skip).limit(limit)

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

    @classmethod
    @trace_fn
    def get_paginated_threads_by_agent(
        cls, agent_class: str, agent_id: str, user_id: str | None = None, skip: int = 0, limit: int = 20
    ) -> list["ThreadEntity"]:
        """
        Get a paginated list of threads that include the specified agent.
        If a user_id is provided, it also filters for threads containing that user.
        """
        query = cls.objects().filter(agents__agent_id=agent_id, agents__agent_class=agent_class)
        if user_id:
            query = query.filter(users__user_id=user_id)
        return query.order_by("-created_at").skip(skip).limit(limit)

    @classmethod
    @trace_fn
    def get_threads_by_users(cls, user_ids: list[str]) -> list["ThreadEntity"]:
        return cls.objects().filter(users__user_id__in=user_ids)

    @classmethod
    @trace_fn
    def get_threads_by_agent(cls, agent_class: str, agent_id: str) -> list["ThreadEntity"]:
        return cls.objects().filter(agents__agent_id=agent_id, agents__agent_class=agent_class)

    @classmethod
    @trace_fn
    def get_thread_ids_for_user(cls, user_id: str) -> list[str]:
        return [str(thread.id) for thread in cls.objects(users__user_id=user_id).only("id")]

    @classmethod
    @trace_fn
    def add_user_to_thread(cls, thread_id: str, user: User) -> Self:
        thread = cls.get_thread_by_id(thread_id)
        thread.users.append(user)
        thread.save()
        return thread

    @classmethod
    @trace_fn
    def add_agent_to_thread(cls, thread_id: str, agent: AgentInstanceRef) -> Self:
        thread = cls.get_thread_by_id(thread_id)
        thread.agents.append(agent)
        thread.save()
        return thread

    @classmethod
    @trace_fn
    def remove_user_from_thread(cls, thread_id: str, user_id: str) -> Self:
        thread = cls.get_thread_by_id(thread_id)
        thread.users = [user for user in thread.users if user.user_id != user_id]
        thread.save()
        return thread

    @classmethod
    @trace_fn
    def remove_agent_from_thread(cls, thread_id: str, agent_class: str, agent_id: str) -> Self:
        thread = cls.get_thread_by_id(thread_id)
        thread.agents = [
            agent for agent in thread.agents if agent.agent_id != agent_id and agent.agent_class != agent_class
        ]
        thread.save()
        return thread

    @trace_fn
    def claim_for_process(self, process_class: str, process_id: str, process_walkthrough_id: str) -> Self:
        self.process_class = process_class
        self.process_id = process_id
        self.process_walkthrough_id = process_walkthrough_id
        self.save()
        return self

    @classmethod
    @trace_fn
    def delete_thread(cls, thread_id: str) -> Self:
        thread = cls.get_thread_by_id(thread_id)
        thread.delete()
        return thread
