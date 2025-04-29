from datetime import datetime
from typing import List, Optional

from bson import ObjectId
from mongoengine import DateTimeField, Document, EmbeddedDocument, EmbeddedDocumentField, ListField, StringField


class User(EmbeddedDocument):
    user_id = StringField(required=True)


class Agent(EmbeddedDocument):
    agent_id = StringField(required=True)
    agent_class = StringField(required=True)


class ThreadEntity(Document):
    meta = {
        "collection": "threads",
        "strict": False,
        "indexes": [
            {"fields": ["users.user_id"]},
            {"fields": ["created_at"]}
        ]
    }
    name = StringField(required=True)
    created_at = DateTimeField(required=True)
    users = ListField(EmbeddedDocumentField(User))
    agents = ListField(EmbeddedDocumentField(Agent))

    @classmethod
    def create_thread(
        cls, name: str, users: List[User], agents: List[Agent], thread_id: Optional[ObjectId] = None
    ) -> "ThreadEntity":
        thread = cls(id=thread_id or ObjectId(), name=name, users=users, agents=agents, created_at=datetime.now())
        thread.save()
        return thread

    @classmethod
    def get_thread_by_id(cls, thread_id: str) -> "ThreadEntity":
        return cls.objects().get(id=ObjectId(thread_id))

    @classmethod
    def get_threads_by_user(cls, user_id: str) -> List["ThreadEntity"]:
        return cls.objects().filter(users__user_id=user_id)

    @classmethod
    def get_threads_by_users(cls, user_ids: List[str]) -> List["ThreadEntity"]:
        return cls.objects().filter(users__user_id__in=user_ids)

    @classmethod
    def add_user_to_thread(cls, thread_id: str, user: User) -> "ThreadEntity":
        thread = cls.get_thread_by_id(thread_id)
        thread.users.append(user)
        thread.save()
        return thread

    @classmethod
    def add_agent_to_thread(cls, thread_id: str, agent: Agent) -> "ThreadEntity":
        thread = cls.get_thread_by_id(thread_id)
        thread.agents.append(agent)
        thread.save()
        return thread

    @classmethod
    def remove_user_from_thread(cls, thread_id: str, user_id: str) -> "ThreadEntity":
        thread = cls.get_thread_by_id(thread_id)
        thread.users = [user for user in thread.users if user.user_id != user_id]
        thread.save()
        return thread

    @classmethod
    def remove_agent_from_thread(cls, thread_id: str, agent_class: str, agent_id: str) -> "ThreadEntity":
        thread = cls.get_thread_by_id(thread_id)
        thread.agents = [
            agent for agent in thread.agents if agent.agent_id != agent_id and agent.agent_class != agent_class
        ]
        thread.save()
        return thread

    @classmethod
    def delete_thread(cls, thread_id: str) -> "ThreadEntity":
        thread = cls.get_thread_by_id(thread_id)
        thread.delete()
        return thread
