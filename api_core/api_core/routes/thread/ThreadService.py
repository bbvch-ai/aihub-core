from typing import List, Optional
from bson import ObjectId

from api_core.routes.thread.dto.ThreadAgentDTO import ThreadAgentDTO
from lib_core.persistence.messaging.entities.ThreadEntity import ThreadEntity, User, Agent


class ThreadService:
    @staticmethod
    def create_thread(name: str, user_ids: List[str], agent_dtos: Optional[List[ThreadAgentDTO]] = None) -> ThreadEntity:
        users = [User(user_id=uid) for uid in user_ids]
        agents = [
            Agent(agent_id=agent.agent_id, agent_class=agent.agent_class) for agent in (agent_dtos or [])
        ]
        return ThreadEntity.create_thread(name=name, users=users, agents=agents)

    @staticmethod
    def get_thread_by_id(thread_id: str) -> ThreadEntity:
        if not ObjectId.is_valid(thread_id):
            raise ValueError("Invalid thread_id provided.")
        return ThreadEntity.get_thread_by_id(thread_id)

    @staticmethod
    def get_threads_for_user(user_id: str) -> List[ThreadEntity]:
        return ThreadEntity.get_threads_by_user(user_id)

    @staticmethod
    def add_agent_to_thread(thread_id: str, agent_id: str, agent_class: str) -> ThreadEntity:
        agent = Agent(agent_id=agent_id, agent_class=agent_class)
        return ThreadEntity.add_agent_to_thread(thread_id, agent)

    @staticmethod
    def remove_agent_from_thread(thread_id: str, agent_id: str) -> ThreadEntity:
        return ThreadEntity.remove_agent_from_thread(thread_id, agent_id)

    @staticmethod
    def add_user_to_thread(thread_id: str, user_id: str) -> ThreadEntity:
        user = User(user_id=user_id)
        return ThreadEntity.add_user_to_thread(thread_id, user)

    @staticmethod
    def remove_user_from_thread(thread_id: str, user_id: str) -> ThreadEntity:
        return ThreadEntity.remove_user_from_thread(thread_id, user_id)

    @staticmethod
    def delete_thread(thread_id: str):
        return ThreadEntity.delete_thread(thread_id)
