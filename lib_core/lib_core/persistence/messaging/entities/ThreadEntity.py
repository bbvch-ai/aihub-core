from typing import List

from bson import ObjectId
from mongoengine import DateTimeField, Document, IntField, ReferenceField, StringField, ListField, EmbeddedDocument, \
    EmbeddedDocumentField


class User(EmbeddedDocument):
    user_id = StringField(required=True)


class Agent(EmbeddedDocument):
    agent_id = StringField(required=True)
    agent_class = StringField(required=True)


class ThreadEntity(Document):
    meta = {
        "collection": "threads",
        "strict": False,
    }
    name = StringField(required=True)
    # created_at = DateTimeField(required=True)
    users = ListField(EmbeddedDocumentField(User), required=True)
    agents = ListField(EmbeddedDocumentField(Agent), required=True)

    @classmethod
    def create_thread(cls, name: str, users: List[User], agents: List[Agent]):
        thread = cls(
            name=name,
            users=users,
            agents=agents
        )
        thread.switch_db("aihub")
        thread.save()
        return thread

    @classmethod
    def get_thread_by_id(cls, thread_id: str):
        return cls.objects().using("aihub").get(id=ObjectId(thread_id))

    @classmethod
    def get_threads_by_user(cls, user_id: str):
        return cls.objects().using("aihub").filter(users__user_id=user_id)

    @classmethod
    def get_threads_by_users(cls, user_ids: List[str]):
        return cls.objects().using("aihub").filter(users__user_id__in=user_ids)

    @classmethod
    def add_user_to_thread(cls, thread_id: str, user: User):
        thread = cls.get_thread_by_id(thread_id)
        thread.users.append(user)
        thread.save()
        return thread

    @classmethod
    def add_agent_to_thread(cls, thread_id: str, agent: Agent):
        thread = cls.get_thread_by_id(thread_id)
        thread.agents.append(agent)
        thread.save()
        return thread

    @classmethod
    def remove_user_from_thread(cls, thread_id: str, user_id: str):
        thread = cls.get_thread_by_id(thread_id)
        thread.users = [user for user in thread.users if user.id != user_id]
        thread.save()
        return thread

    @classmethod
    def remove_agent_from_thread(cls, thread_id: str, agent_id: str):
        thread = cls.get_thread_by_id(thread_id)
        thread.agents = [agent for agent in thread.agents if agent.id != agent_id]
        thread.save()
        return thread

    @classmethod
    def delete_thread(cls, thread_id: str):
        thread = cls.get_thread_by_id(thread_id)
        thread.delete()
        return thread
