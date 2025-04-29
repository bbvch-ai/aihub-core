from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple, Union

from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.persistence.agents.AgentEntity import AgentEntity
from aihub_lib.persistence.messaging.entities.PersistedEventEntity import PersistedEventEntity
from aihub_lib.persistence.messaging.entities.ThreadEntity import Agent, ThreadEntity, User
from bson import ObjectId

from aihub_api.routes.agent.dto.AgentDTO import AgentDTO, MinimalAgentDTO
from aihub_api.routes.event.EventService import EventService
from aihub_api.routes.thread.dto.ThreadAgentDTO import ThreadAgentDTO
from aihub_api.routes.thread.dto.ThreadResponse import DisplayStatistics, EventStatistics, RunStatistics, ThreadResponse
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
    def calculate_event_statistics(events: List[PersistedEventEntity]) -> EventStatistics:
        """
        Calculate statistics for a list of events.
        Returns an EventStatistics object with statistics like started_at, ended_at, latency, n_events, etc.
        """
        stats = EventStatistics(n_events=len(events))

        # Count events and track times
        for event in events:
            # Check event types
            if "StartEvent" in event.event_parents:
                stats.start_events += 1
            if "StopEvent" in event.event_parents:
                stats.stop_events += 1
            if "ExceptionEvent" in event.event_parents or event.event_name == "ExceptionEvent":
                stats.exception_events += 1
            if "HumanInTheLoopRequestEvent" in event.event_parents:
                stats.hitl_request_events += 1
            if "HumanInTheLoopResponseEvent" in event.event_parents:
                stats.hitl_response_events += 1
            if "BotInTheLoopRequestEvent" in event.event_parents:
                stats.bitl_request_events += 1
            if "BotInTheLoopResponseEvent" in event.event_parents:
                stats.bitl_response_events += 1
            if "AgentInTheLoopRequestEvent" in event.event_parents:
                stats.aitl_request_events += 1
            if "AgentInTheLoopResponseEvent" in event.event_parents:
                stats.aitl_response_events += 1

            # Track event times
            if "created_at" in event.event_data:
                event_time = None
                created_at = event.event_data["created_at"]

                # Handle different types of created_at values
                if isinstance(created_at, (int, float)):
                    # Convert timestamp to datetime
                    event_time = datetime.fromtimestamp(created_at / 1_000_000_000)
                elif isinstance(created_at, str):
                    try:
                        # Try to parse ISO format string
                        event_time = datetime.fromisoformat(created_at.rstrip("Z"))
                    except ValueError:
                        pass

                if event_time:
                    if stats.first_event_time is None or event_time < stats.first_event_time:
                        stats.first_event_time = event_time
                    if stats.latest_event_time is None or event_time > stats.latest_event_time:
                        stats.latest_event_time = event_time

        # Calculate derived statistics
        stats.has_pending = stats.start_events > stats.stop_events
        stats.has_errors = stats.exception_events > 0
        stats.is_hitl = stats.hitl_request_events > 0
        stats.open_hitl = stats.hitl_request_events > stats.hitl_response_events
        stats.is_bitl = stats.bitl_request_events > 0
        stats.open_bitl = stats.bitl_request_events > stats.bitl_response_events
        stats.is_aitl = stats.aitl_request_events > 0
        stats.open_aitl = stats.aitl_request_events > stats.aitl_response_events

        # Calculate latency if we have both start and end times
        if stats.first_event_time and stats.latest_event_time:
            stats.latency = (stats.latest_event_time - stats.first_event_time).total_seconds()
            stats.started_at = stats.first_event_time
            stats.ended_at = stats.latest_event_time

        return stats

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
        5. Calculate enhanced statistics (displays, runs, participating agents, LLM costs).
        """
        agent_dtos = []
        for agent in entity.agents:
            agent_entity = AgentEntity.get_agent(
                agent_class=agent.agent_class,
                agent_id=agent.agent_id,
            )
            agent_dto = MinimalAgentDTO.from_entity(agent_entity, t)
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

        if not events:
            return response

        # Calculate thread-level statistics using the helper function
        thread_stats = ThreadService.calculate_event_statistics(events)

        # Update response with thread-level statistics
        response.num_events = thread_stats.n_events
        response.num_turns = thread_stats.start_events
        response.has_pending = thread_stats.has_pending
        response.has_errors = thread_stats.has_errors
        response.is_hitl = thread_stats.is_hitl
        response.open_hitl = thread_stats.open_hitl
        response.is_bitl = thread_stats.is_bitl
        response.open_bitl = thread_stats.open_bitl
        response.is_aitl = thread_stats.is_aitl
        response.open_aitl = thread_stats.open_aitl
        response.latency = thread_stats.latency

        # Set interaction times
        if thread_stats.first_event_time:
            response.first_interaction = thread_stats.first_event_time.isoformat() + "Z"
        if thread_stats.latest_event_time:
            response.latest_interaction = thread_stats.latest_event_time.isoformat() + "Z"

        # Group events by display_id and run_id
        displays_dict = {}
        participating_agent_ids = set()
        llm_cost = 0.0

        for event in events:
            # Group events by display_id and run_id
            display_id = event.display_id
            run_id = event.run_id

            if display_id not in displays_dict:
                displays_dict[display_id] = {"events": [], "runs": {}}

            displays_dict[display_id]["events"].append(event)

            if run_id not in displays_dict[display_id]["runs"]:
                displays_dict[display_id]["runs"][run_id] = []

            displays_dict[display_id]["runs"][run_id].append(event)

            # Track participating agents
            participating_agent_ids.add((event.agent_class, event.agent_id))

            # Calculate LLM costs
            if "LLMCostEvent" in event.event_parents or event.event_name == "LLMCostEvent":
                llm_cost += event.event_data.get("prompt_tokens_costs", 0)
                llm_cost += event.event_data.get("completion_tokens_costs", 0)
                llm_cost += event.event_data.get("embedding_tokens_costs", 0)

        # Create display statistics
        displays = []
        for display_id, display_data in displays_dict.items():
            display_events = display_data["events"]
            display_stats = ThreadService.calculate_event_statistics(display_events)

            # Create runs statistics
            runs = []
            for run_id, run_events in display_data["runs"].items():
                run_stats = ThreadService.calculate_event_statistics(run_events)

                # Format datetime objects to ISO strings
                started_at = None
                ended_at = None
                if run_stats.started_at:
                    started_at = run_stats.started_at.isoformat() + "Z"
                if run_stats.ended_at:
                    ended_at = run_stats.ended_at.isoformat() + "Z"

                start_event = next(event for event in run_events if "StartEvent" in event.event_parents)

                agent_entity = AgentEntity.get_agent(
                    agent_class=start_event.agent_class,
                    agent_id=start_event.agent_id,
                )
                agent_dto = MinimalAgentDTO.from_entity(agent_entity, t)

                runs.append(RunStatistics(
                    agent=agent_dto,
                    run_id=run_id,
                    started_at=started_at,
                    ended_at=ended_at,
                    latency=run_stats.latency,
                    n_events=run_stats.n_events,
                    has_errors=run_stats.has_errors,
                    has_pending=run_stats.has_pending,
                    is_hitl=run_stats.is_hitl,
                    open_hitl=run_stats.open_hitl,
                    is_bitl=run_stats.is_bitl,
                    open_bitl=run_stats.open_bitl,
                    is_aitl=run_stats.is_aitl,
                    open_aitl=run_stats.open_aitl
                ))

            # Format datetime objects to ISO strings
            started_at = None
            ended_at = None
            if display_stats.started_at:
                started_at = display_stats.started_at.isoformat() + "Z"
            if display_stats.ended_at:
                ended_at = display_stats.ended_at.isoformat() + "Z"

            displays.append(DisplayStatistics(
                display_id=display_id,
                started_at=started_at,
                ended_at=ended_at,
                latency=display_stats.latency,
                n_events=display_stats.n_events,
                has_errors=display_stats.has_errors,
                has_pending=display_stats.has_pending,
                is_hitl=display_stats.is_hitl,
                open_hitl=display_stats.open_hitl,
                is_bitl=display_stats.is_bitl,
                open_bitl=display_stats.open_bitl,
                is_aitl=display_stats.is_aitl,
                open_aitl=display_stats.open_aitl,
                runs=runs
            ))

        # Get participating agents
        participating_agents = []
        for agent_class, agent_id in participating_agent_ids:
            try:
                agent_entity = AgentEntity.get_agent(agent_class=agent_class, agent_id=agent_id)
                agent_dto = MinimalAgentDTO.from_entity(agent_entity, t)
                participating_agents.append(agent_dto)
            except Exception:
                # Skip agents that can't be found
                pass

        # Update response with new fields
        response.displays = displays
        response.participating_agents = participating_agents
        response.llm_cost = llm_cost

        return response
