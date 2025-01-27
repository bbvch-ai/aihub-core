import asyncio
from typing import List, Optional
from bson import ObjectId
from nats.aio.client import Client as NATS

from aihub_api.routes.agent.AgentService import AgentService
from aihub_api.routes.thread.dto.ThreadAgentDTO import ThreadAgentDTO
from aihub_api.routes.thread.dto.ThreadResponse import ThreadResponse
from aihub_api.routes.user.UserService import UserService
from aihub_lib.persistence.messaging.entities.ThreadEntity import ThreadEntity, User, Agent


class ThreadService:
    """
    A service layer that handles business logic for thread operations:
    - Creating threads with specified users and agents.
    - Retrieving threads by ID or by user.
    - Adding or removing agents and users from existing threads.
    - Converting internal ThreadEntity objects to ThreadResponse DTOs.

    ### Why ThreadService?
    Isolating thread logic here keeps controllers slim and focused on request/response handling.
    ThreadService:
    - Interacts with the persistence layer (ThreadEntity).
    - Uses AgentService to fetch agent details for a thread.
    - Uses UserService to fetch user data, ensuring all responses are enriched with user and agent info.

    ### Caching and Performance
    Currently, no caching is implemented here. If needed, caching logic can be added later.
    """

    @staticmethod
    async def create_thread(
        nc: NATS, name: str, user_ids: List[str], agent_dtos: Optional[List[ThreadAgentDTO]] = None
    ) -> ThreadResponse:
        users = [User(user_id=uid) for uid in user_ids]
        agents = [Agent(agent_id=agent.agent_id, agent_class=agent.agent_class) for agent in (agent_dtos or [])]
        created_thread = ThreadEntity.create_thread(name=name, users=users, agents=agents)
        return await ThreadService.thread_response_from_entity(created_thread, nc)

    @staticmethod
    async def get_thread_by_id(nc: NATS, thread_id: str) -> ThreadResponse:
        if not ObjectId.is_valid(thread_id):
            raise ValueError("Invalid thread_id provided.")
        thread = ThreadEntity.get_thread_by_id(thread_id)
        return await ThreadService.thread_response_from_entity(thread, nc)

    @staticmethod
    async def get_threads_for_user(nc: NATS, user_id: str) -> List[ThreadResponse]:
        threads = ThreadEntity.get_threads_by_user(user_id)
        return [await ThreadService.thread_response_from_entity(t, nc) for t in threads]

    @staticmethod
    async def add_agent_to_thread(nc: NATS, thread_id: str, agent_id: str, agent_class: str) -> ThreadResponse:
        agent = Agent(agent_id=agent_id, agent_class=agent_class)
        thread = ThreadEntity.add_agent_to_thread(thread_id, agent)
        return await ThreadService.thread_response_from_entity(thread, nc)

    @staticmethod
    async def remove_agent_from_thread(nc: NATS, thread_id: str, agent_class: str, agent_id: str) -> ThreadResponse:
        thread = ThreadEntity.remove_agent_from_thread(thread_id, agent_class, agent_id)
        return await ThreadService.thread_response_from_entity(thread, nc)

    @staticmethod
    async def add_user_to_thread(nc: NATS, thread_id: str, user_id: str) -> ThreadResponse:
        user = User(user_id=user_id)
        thread = ThreadEntity.add_user_to_thread(thread_id, user)
        return await ThreadService.thread_response_from_entity(thread, nc)

    @staticmethod
    async def remove_user_from_thread(nc: NATS, thread_id: str, user_id: str) -> ThreadResponse:
        thread = ThreadEntity.remove_user_from_thread(thread_id, user_id)
        return await ThreadService.thread_response_from_entity(thread, nc)

    @staticmethod
    async def delete_thread(nc: NATS, thread_id: str) -> ThreadResponse:
        thread = ThreadEntity.delete_thread(thread_id)
        return await ThreadService.thread_response_from_entity(thread, nc)

    @staticmethod
    async def thread_response_from_entity(entity: ThreadEntity, nc: NATS) -> ThreadResponse:
        """
        Converts a ThreadEntity into a ThreadResponse:
        1. Fetch agent details (using AgentService).
        2. Fetch user details (using UserService).
        3. Construct a ThreadResponse DTO containing all details.
        """
        agents = await asyncio.gather(
            *(AgentService.get_agent(nc, agent.agent_class, agent.agent_id) for agent in entity.agents)
        )

        return ThreadResponse(
            id=str(entity.id),
            name=entity.name,
            users=[UserService.get_user_by_oid(user.user_id) for user in entity.users],
            agents=agents,
        )
