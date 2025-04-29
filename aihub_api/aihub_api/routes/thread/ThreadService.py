from datetime import datetime
from typing import List, Optional

from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.persistence.agents.AgentEntity import AgentEntity
from aihub_lib.persistence.messaging.entities.ThreadEntity import Agent, ThreadEntity, User
from bson import ObjectId

from aihub_api.routes.agent.dto.AgentDTO import AgentDTO
from aihub_api.routes.event.EventService import EventService
from aihub_api.routes.thread.dto.ThreadAgentDTO import ThreadAgentDTO
from aihub_api.routes.thread.dto.ThreadResponse import ThreadResponse
from aihub_api.routes.user.UserService import UserService


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
    def create_thread(
        name: str, user_ids: List[str], t: LocaleHandler, agent_dtos: Optional[List[ThreadAgentDTO]] = None
    ) -> ThreadResponse:
        users = [User(user_id=uid) for uid in user_ids]
        agents = [Agent(agent_id=agent.agent_id, agent_class=agent.agent_class) for agent in (agent_dtos or [])]
        created_thread = ThreadEntity.create_thread(name=name, users=users, agents=agents)
        return ThreadService.thread_response_from_entity(created_thread, t)

    @staticmethod
    def get_thread_by_id(thread_id: str, t: LocaleHandler) -> ThreadResponse:
        if not ObjectId.is_valid(thread_id):
            raise ValueError("Invalid thread_id provided.")
        thread = ThreadEntity.get_thread_by_id(thread_id)
        return ThreadService.thread_response_from_entity(thread, t)

    @staticmethod
    def get_threads_for_user(user_id: str, t: LocaleHandler) -> List[ThreadResponse]:
        threads = ThreadEntity.get_threads_by_user(user_id)
        return [ThreadService.thread_response_from_entity(thread, t) for thread in threads]

    @staticmethod
    def get_threads_for_agent(agent_class: str, agent_id: str, t: LocaleHandler) -> List[ThreadResponse]:
        threads = ThreadEntity.get_threads_by_agent(agent_class, agent_id)
        return [ThreadService.thread_response_from_entity(thread, t) for thread in threads]

    @staticmethod
    def add_agent_to_thread(thread_id: str, agent_id: str, agent_class: str, t: LocaleHandler) -> ThreadResponse:
        agent = Agent(agent_id=agent_id, agent_class=agent_class)
        thread = ThreadEntity.add_agent_to_thread(thread_id, agent)
        return ThreadService.thread_response_from_entity(thread, t)

    @staticmethod
    def remove_agent_from_thread(thread_id: str, agent_class: str, agent_id: str, t: LocaleHandler) -> ThreadResponse:
        thread = ThreadEntity.remove_agent_from_thread(thread_id, agent_class, agent_id)
        return ThreadService.thread_response_from_entity(thread, t)

    @staticmethod
    def add_user_to_thread(thread_id: str, user_id: str, t: LocaleHandler) -> ThreadResponse:
        user = User(user_id=user_id)
        thread = ThreadEntity.add_user_to_thread(thread_id, user)
        return ThreadService.thread_response_from_entity(thread, t)

    @staticmethod
    def remove_user_from_thread(thread_id: str, user_id: str, t: LocaleHandler) -> ThreadResponse:
        thread = ThreadEntity.remove_user_from_thread(thread_id, user_id)
        return ThreadService.thread_response_from_entity(thread, t)

    @staticmethod
    def delete_thread(thread_id: str, t: LocaleHandler) -> ThreadResponse:
        thread = ThreadEntity.delete_thread(thread_id)
        return ThreadService.thread_response_from_entity(thread, t)

    @staticmethod
    def thread_response_from_entity(entity: ThreadEntity, t: LocaleHandler) -> ThreadResponse:
        """
        Converts a ThreadEntity into a ThreadResponse:
        1. Fetch agent details (using AgentService).
        2. Fetch user details (using UserService).
        3. Fetch event statistics for the thread.
        4. Construct a ThreadResponse DTO containing all details.
        """
        agent_dtos = []
        for agent in entity.agents:
            agent_entity = AgentEntity.get_agent(
                agent_class=agent.agent_class,
                agent_id=agent.agent_id,
            )
            agent_dto = AgentDTO.from_entity(agent_entity, t)
            agent_dtos.append(agent_dto)

        # Create the base response
        response = ThreadResponse(
            id=str(entity.id),
            created_at=entity.created_at.isoformat() + "Z",  # Add Z to indicate UTC
            name=entity.name,
            users=[UserService.get_user_by_oid(user.user_id) for user in entity.users],
            agents=agent_dtos,
        )

        # Get all events for the thread to calculate statistics
        events = EventService.get_all_thread_events(str(entity.id))

        # Calculate statistics
        if events:
            response.num_events = len(events)

            # Count different types of events
            start_events = 0
            stop_events = 0
            exception_events = 0
            hitl_request_events = 0
            hitl_response_events = 0
            bitl_request_events = 0
            bitl_response_events = 0
            aitl_request_events = 0
            aitl_response_events = 0

            # Track first and latest interaction
            first_event_time = None
            latest_event_time = None

            for event in events:
                # Check event types
                if "StartEvent" in event.event_parents:
                    start_events += 1
                if "StopEvent" in event.event_parents:
                    stop_events += 1
                if "ExceptionEvent" in event.event_parents or event.event_name == "ExceptionEvent":
                    exception_events += 1
                if "HumanInTheLoopRequestEvent" in event.event_parents:
                    hitl_request_events += 1
                if "HumanInTheLoopResponseEvent" in event.event_parents:
                    hitl_response_events += 1
                if "BotInTheLoopRequestEvent" in event.event_parents:
                    bitl_request_events += 1
                if "BotInTheLoopResponseEvent" in event.event_parents:
                    bitl_response_events += 1
                if "AgentInTheLoopRequestEvent" in event.event_parents:
                    aitl_request_events += 1
                if "AgentInTheLoopResponseEvent" in event.event_parents:
                    aitl_response_events += 1

                # Track event times
                if "created_at" in event.event_data:
                    event_time = event.event_data["created_at"] / 1_000_000_000
                    event_time = datetime.fromtimestamp(event_time)

                    if first_event_time is None or event_time < first_event_time:
                        first_event_time = event_time
                    if latest_event_time is None or event_time > latest_event_time:
                        latest_event_time = event_time

            # Set statistics in response
            response.num_turns = start_events
            response.has_pending = start_events > stop_events
            response.has_errors = exception_events > 0
            response.is_hitl = hitl_request_events > 0
            response.open_hitl = hitl_request_events > hitl_response_events
            response.is_bitl = bitl_request_events > 0
            response.open_bitl = bitl_request_events > bitl_response_events
            response.is_aitl = aitl_request_events > 0
            response.open_aitl = aitl_request_events > aitl_response_events

            # Set interaction times
            if first_event_time:
                response.first_interaction = first_event_time.isoformat() + "Z"
            if latest_event_time:
                response.latest_interaction = latest_event_time.isoformat() + "Z"

        return response
