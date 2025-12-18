import asyncio
import logging
from datetime import UTC, datetime

from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn
from aihub_lib.nats.events import BaseEvent
from aihub_lib.nats.events.human_in_the_loop.request.HumanInTheLoopRequestEvent import HumanInTheLoopRequestEvent
from aihub_lib.nats.events.human_in_the_loop.response.HumanInTheLoopResponseEvent import HumanInTheLoopResponseEvent
from aihub_lib.persistence.messaging.entities.PersistedAgentEventEntity import PersistedAgentEventEntity
from aihub_lib.persistence.messaging.entities.ThreadEntity import Agent, ThreadEntity, User
from bson import ObjectId
from cachetools import TTLCache, cached
from llama_index.core.base.llms.types import AudioBlock, ImageBlock, TextBlock
from mongoengine import DoesNotExist
from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionContentPartImageParam,
    ChatCompletionContentPartInputAudioParam,
    ChatCompletionContentPartTextParam,
    ChatCompletionMessageParam,
    ChatCompletionUserMessageParam,
)
from openai.types.chat.chat_completion_content_part_image_param import ImageURL
from openai.types.chat.chat_completion_content_part_input_audio_param import InputAudio

from aihub_api.routes.agent.dto.AgentIdentifier import AgentIdentifier
from aihub_api.routes.agent.dto.MinimalAgentDTO import MinimalAgentDTO
from aihub_api.routes.event.EventService import EventService
from aihub_api.routes.openai.dto.HistoryResponse import HistoryResponse
from aihub_api.routes.thread.dto.OpenChatHitlResponse import OpenChatHitlResponse
from aihub_api.routes.thread.dto.statistics.CalculatedThreadStats import CalculatedThreadStats
from aihub_api.routes.thread.dto.statistics.DisplayStatistics import DisplayStatistics
from aihub_api.routes.thread.dto.statistics.IntermediateDisplayStats import IntermediateDisplayStats
from aihub_api.routes.thread.dto.statistics.ProcessedRunResults import ProcessedRunResults
from aihub_api.routes.thread.dto.statistics.RunStatistics import RunStatistics
from aihub_api.routes.thread.dto.ThreadAgentDTO import ThreadAgentDTO
from aihub_api.routes.thread.dto.ThreadDTO import ThreadDTO
from aihub_api.routes.user.dto.MinimalUserDTO import MinimalUserDTO
from aihub_api.routes.user.UserService import UserService
from aihub_api.sockets.events.server_to_user.ContextualizedAgentEvent import ContextualizedAgentEvent

logger = logging.getLogger(__name__)


class ThreadService:
    """
    A service layer that handles business logic for thread operations.
    """

    @staticmethod
    @trace_fn
    async def create_thread(
        name: str,
        user_ids: list[str],
        t: LocaleHandler,
        agent_dtos: list[ThreadAgentDTO] | None = None,
    ) -> ThreadDTO:
        users = [User(user_id=user_id) for user_id in user_ids]
        agents = [Agent(agent_id=agent.agent_id, agent_class=agent.agent_class) for agent in (agent_dtos or [])]
        created_thread = ThreadEntity.create_thread(name=name, users=users, agents=agents)
        return await ThreadService.thread_response_from_entity(created_thread, t)

    @staticmethod
    @trace_fn
    async def get_thread_by_id(
        thread_id: str,
        t: LocaleHandler,
    ) -> ThreadDTO:
        if not ObjectId.is_valid(thread_id):
            raise ValueError("Invalid thread_id provided.")
        thread = ThreadEntity.get_thread_by_id(thread_id)
        return await ThreadService.thread_response_from_entity(thread, t)

    @staticmethod
    @trace_fn
    async def get_paginated_threads_for_user(
        user_id: str,
        t: LocaleHandler,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[int, list[ThreadDTO]]:
        """Returns a paginated list of threads that the user is a member of."""
        skip = (page - 1) * page_size
        total = ThreadEntity.count_threads_by_user(user_id)
        threads = ThreadEntity.get_paginated_threads_by_user(user_id, skip=skip, limit=page_size)
        thread_dtos = await asyncio.gather(
            *(ThreadService.thread_response_from_entity(thread, t) for thread in threads)
        )
        return total, thread_dtos

    @staticmethod
    @trace_fn
    async def get_paginated_threads_for_agent(
        agent_class: str,
        agent_id: str,
        t: LocaleHandler,
        page: int = 1,
        page_size: int = 20,
        user_id: str | None = None,
    ) -> tuple[int, list[ThreadDTO]]:
        """
        Returns a paginated list of threads that a specific agent is part of.
        """
        skip = (page - 1) * page_size
        total = ThreadEntity.count_threads_by_agent(agent_class, agent_id)
        threads = ThreadEntity.get_paginated_threads_by_agent(
            agent_class, agent_id, skip=skip, limit=page_size, user_id=user_id
        )
        thread_dtos = await asyncio.gather(
            *(ThreadService.thread_response_from_entity(thread, t) for thread in threads)
        )
        return total, thread_dtos

    @staticmethod
    @trace_fn
    async def add_agent_to_thread(
        thread_id: str,
        agent_id: str,
        agent_class: str,
        t: LocaleHandler,
    ) -> ThreadDTO:
        agent = Agent(agent_id=agent_id, agent_class=agent_class)
        thread = ThreadEntity.add_agent_to_thread(thread_id, agent)
        return await ThreadService.thread_response_from_entity(thread, t)

    @staticmethod
    @trace_fn
    async def thread_as_message_history(thread_id: str) -> HistoryResponse:
        persisted_events = EventService.get_all_thread_display_events(thread_id)
        contextualized_events = [ContextualizedAgentEvent.from_persisted_event(event) for event in persisted_events]

        messages: list[ChatCompletionMessageParam] = []

        def is_user_event(event: BaseEvent) -> bool:
            return event.is_user_message_event or event.is_hitl_response_event

        def is_agent_event(event: BaseEvent) -> bool:
            return event.is_chunk_event or event.is_hitl_response_event

        continue_chunk = False

        for contextualized_event in contextualized_events:
            event = contextualized_event.event

            if is_user_event(event):
                continue_chunk = False

                if len(messages) == 0 or messages[-1]["role"] != "user":
                    messages.append(ChatCompletionUserMessageParam(role="user", content=[]))

                current_message = messages[-1]
                if event.is_user_message_event and len(event.messages) > 0:
                    for block in event.messages[-1].blocks:
                        if isinstance(block, TextBlock):
                            current_message["content"].append(
                                ChatCompletionContentPartTextParam(text=block.text, type="text")
                            )
                        if isinstance(block, ImageBlock):
                            current_message["content"].append(
                                ChatCompletionContentPartImageParam(
                                    image_url=ImageURL(url=str(block.url)), type="image_url"
                                )
                            )
                        if isinstance(block, AudioBlock):
                            current_message["content"].append(
                                ChatCompletionContentPartInputAudioParam(
                                    input_audio=InputAudio(data=block.audio, format=block.format), type="input_audio"
                                )
                            )

                if event.is_hitl_response_event:
                    current_message["content"].append(
                        ChatCompletionContentPartTextParam(text=event.response, type="text")
                    )

            if is_agent_event(event):
                if len(messages) == 0 or messages[-1]["role"] != "assistant":
                    messages.append(ChatCompletionAssistantMessageParam(role="assistant", content=[]))

                current_message = messages[-1]
                if event.is_chunk_event:
                    if continue_chunk:
                        current_message["content"][-1]["text"] += event.content
                    else:
                        current_message["content"].append(
                            ChatCompletionContentPartTextParam(text=event.content, type="text")
                        )
                        continue_chunk = True

                if event.is_hitl_response_event:
                    continue_chunk = False
                    current_message["content"].append(
                        ChatCompletionContentPartTextParam(text=event.response, type="text")
                    )

        return HistoryResponse(messages=messages)

    @staticmethod
    @trace_fn
    def get_open_chat_hitl(thread_id: str) -> OpenChatHitlResponse:
        """
        Returns the oldest open chat HITL request for a thread, if any.

        A chat HITL is open when it has not been responded to. Only HITL requests
        with hitl_type == "chat" are considered.
        """
        hitl_request_entities = PersistedAgentEventEntity.human_in_the_loop_request_events_for_thread(thread_id)
        hitl_response_entities = PersistedAgentEventEntity.human_in_the_loop_response_events_for_thread(thread_id)

        # Deserialize to typed Pydantic objects
        hitl_requests = [HumanInTheLoopRequestEvent.deserialize_event(e.event_data) for e in hitl_request_entities]
        hitl_responses = [HumanInTheLoopResponseEvent.deserialize_event(e.event_data) for e in hitl_response_entities]

        # Build set of responded request event IDs using typed access
        responded_request_ids: set[str] = {response.request_event.event_id for response in hitl_responses}

        # Find the first open chat HITL request
        for request in hitl_requests:
            if request.hitl_type == "chat" and request.event_id not in responded_request_ids:
                return OpenChatHitlResponse(has_open_chat_hitl=True, hitl_request=request)

        return OpenChatHitlResponse(has_open_chat_hitl=False, hitl_request=None)

    @staticmethod
    @trace_fn
    async def remove_agent_from_thread(
        thread_id: str,
        agent_class: str,
        agent_id: str,
        t: LocaleHandler,
    ) -> ThreadDTO:
        thread = ThreadEntity.remove_agent_from_thread(thread_id, agent_class, agent_id)
        return await ThreadService.thread_response_from_entity(thread, t)

    @staticmethod
    @trace_fn
    async def add_user_to_thread(
        thread_id: str,
        user_id: str,
        t: LocaleHandler,
    ) -> ThreadDTO:
        user = User(user_id=user_id)
        thread = ThreadEntity.add_user_to_thread(thread_id, user)
        return await ThreadService.thread_response_from_entity(thread, t)

    @staticmethod
    @trace_fn
    async def remove_user_from_thread(thread_id: str, user_id: str, t: LocaleHandler) -> ThreadDTO:
        thread = ThreadEntity.remove_user_from_thread(thread_id, user_id)
        return await ThreadService.thread_response_from_entity(thread, t)

    @staticmethod
    @trace_fn
    async def delete_thread(thread_id: str, t: LocaleHandler) -> ThreadDTO:
        thread = ThreadEntity.delete_thread(thread_id)
        return await ThreadService.thread_response_from_entity(thread, t)

    @staticmethod
    @cached(TTLCache(maxsize=128, ttl=60))
    @trace_fn
    def _fetch_minimal_agent_dto(agent_class: str, agent_id: str, t: LocaleHandler) -> MinimalAgentDTO | None:
        """
        Fetches agent details and converts to MinimalAgentDTO.
        Returns None if the agent cannot be found or fetching fails.
        """
        try:
            from aihub_api.routes.agent.AgentService import AgentService

            return AgentService.get_minimal_agent(agent_class, agent_id, t)
        except DoesNotExist:
            logger.warning(f"Agent not found: {agent_class}/{agent_id}")
            return None
        except Exception as e:
            logger.exception(f"Error fetching agent {agent_class}/{agent_id}: {e}")
            return None

    @staticmethod
    @trace_fn
    def _process_aggregated_runs(aggregated_runs: list[dict], t: "LocaleHandler") -> ProcessedRunResults:
        """
        Processes raw aggregation results into intermediate display statistics
        and collects unique participating agent identifiers.
        """
        results = ProcessedRunResults()

        for run_data in aggregated_runs:
            display_id = run_data.get("display_id")
            if not display_id:
                logger.warning(f"Skipping run with missing display_id: {run_data.get('run_id')}")
                continue

            # Get or create the intermediate aggregator for the display
            if display_id not in results.display_aggregates:
                results.display_aggregates[display_id] = IntermediateDisplayStats(display_id=display_id)
            display_agg = results.display_aggregates[display_id]

            # Update counts, times, and cost in the intermediate aggregator
            display_agg.update_from_run_data(run_data)

            # Attempt to fetch the agent that started the run using the cached method
            start_agent_class = run_data.get("start_agent_class")
            start_agent_id = run_data.get("start_agent_id")
            run_agent_dto = ThreadService._fetch_minimal_agent_dto(start_agent_class, start_agent_id, t)

            # Create and add the RunStatistics DTO if the agent was found
            if run_agent_dto:
                try:
                    run_stat_dto = RunStatistics.from_run_data(run_data, run_agent_dto)
                    display_agg.add_run_dto(run_stat_dto)
                except Exception as e:
                    # Log validation or other errors during DTO creation
                    logger.exception(f"Error creating RunStatistics DTO for run {run_data.get('run_id')}: {e}")
            else:
                logger.warning(
                    f"RunStatistics DTO skipped for run {run_data.get('run_id')} because starting agent "
                    f"{start_agent_class}/{start_agent_id} could not be fetched."
                )

            # Collect unique identifiers of all agents participating in the run
            for agent_info in run_data.get("participating_agents_in_run", []):
                pa_class = agent_info.get("agent_class")
                pa_id = agent_info.get("agent_id")
                if pa_class and pa_id:
                    results.participating_agent_ids.add(AgentIdentifier(agent_class=pa_class, agent_id=pa_id))

        return results

    @staticmethod
    @trace_fn
    def _calculate_overall_thread_stats(
        display_aggregates: dict[str, IntermediateDisplayStats],
    ) -> CalculatedThreadStats:
        """
        Calculates overall thread statistics by summing up intermediate display stats.
        """
        stats = CalculatedThreadStats()  # Initialize the stats container
        if not display_aggregates:
            return stats  # Return default empty stats if no aggregates

        all_start_times: list[datetime] = []
        all_end_times: list[datetime] = []

        for agg in display_aggregates.values():
            stats.num_events += agg.n_events
            stats.num_turns += agg.start_events
            stats.llm_cost += agg.llm_cost
            # Sum up individual event counts for overall flags
            stats.has_errors = stats.has_errors or (agg.exception_events > 0)
            stats.is_hitl = stats.is_hitl or (agg.hitl_request_events > 0)
            stats.open_hitl = stats.open_hitl or (agg.hitl_request_events > agg.hitl_response_events)
            stats.is_bitl = stats.is_bitl or (agg.bitl_request_events > 0)
            stats.open_bitl = stats.open_bitl or (agg.bitl_request_events > agg.bitl_response_events)
            stats.is_aitl = stats.is_aitl or (agg.aitl_request_events > 0)
            stats.open_aitl = stats.open_aitl or (agg.aitl_request_events > agg.aitl_response_events)
            stats.has_pending = stats.has_pending or (agg.start_events > (agg.stop_events + agg.exception_events))

            if agg.first_event_time:
                all_start_times.append(agg.first_event_time)
            if agg.latest_event_time:
                all_end_times.append(agg.latest_event_time)

        # Calculate overall timing
        if all_start_times:
            stats.first_interaction_dt = min(all_start_times)
        if all_end_times:
            stats.latest_interaction_dt = max(all_end_times)
        if stats.first_interaction_dt and stats.latest_interaction_dt:
            stats.duration = (stats.latest_interaction_dt - stats.first_interaction_dt).total_seconds()

        return stats

    @staticmethod
    @trace_fn
    async def thread_response_from_entity(entity: ThreadEntity, t: "LocaleHandler") -> ThreadDTO:
        """
        Constructs the comprehensive ThreadDTO from a ThreadEntity, including
        aggregated event statistics and participating agent/user information.
        """
        # 1. Fetch initial users and agents associated directly with the thread
        #    Leverages the cached agent fetcher.
        initial_agent_dtos: list[MinimalAgentDTO] = []
        for agent_ref in entity.agents:
            dto = ThreadService._fetch_minimal_agent_dto(agent_ref.agent_class, agent_ref.agent_id, t)
            if dto:
                initial_agent_dtos.append(dto)

        user_dtos: list[MinimalUserDTO] = []
        for user_ref in entity.users:
            try:
                user_dto = await UserService.get_user_by_oid(user_ref.user_id)
                if user_dto:
                    user_dtos.append(user_dto)
            except Exception as e:
                logger.warning(f"Could not fetch user {user_ref.user_id}: {e}")

        response = ThreadDTO(
            id=str(entity.id),
            created_at=(
                entity.created_at.replace(tzinfo=UTC) if entity.created_at.tzinfo is None else entity.created_at
            )
            .isoformat()
            .replace("+00:00", "Z"),
            name=entity.name,
            users=user_dtos,
            agents=sorted(initial_agent_dtos, key=lambda a: (a.agent_class, a.agent_id)),
        )

        # 2. Get aggregated run statistics from the database
        try:
            aggregated_runs: list[dict] = PersistedAgentEventEntity.get_aggregated_run_statistics(str(entity.id))
        except Exception as e:
            logger.exception(f"Failed to get aggregated run statistics for thread {entity.id}: {e}")
            return response

        if not aggregated_runs:
            return response

        # 3. Process raw run data into intermediate structures
        processed_results = ThreadService._process_aggregated_runs(aggregated_runs, t)

        # 4. Create final Display DTOs from intermediate aggregates
        final_display_dtos: list[DisplayStatistics] = []
        for intermediate_stat in processed_results.display_aggregates.values():
            try:
                display_dto = DisplayStatistics.from_intermediate(intermediate_stat)
                final_display_dtos.append(display_dto)
            except Exception as e:
                logger.exception(
                    f"Error creating DisplayStatistics DTO for display {intermediate_stat.display_id}: {e}"
                )

        min_utc_datetime = datetime.min.replace(tzinfo=UTC)

        def display_sort_key(display: DisplayStatistics) -> datetime:
            if display.started_at:
                try:
                    return datetime.fromisoformat(display.started_at.replace("Z", "+00:00"))
                except (ValueError, TypeError):
                    logger.warning(f"Could not parse display start time for sorting: {display.started_at}")
                    return min_utc_datetime
            return min_utc_datetime

        response.displays = sorted(final_display_dtos, key=display_sort_key)

        # 5. Fetch DTOs for all unique participating agents
        final_participating_agents: list[MinimalAgentDTO] = []
        for agent_id in processed_results.participating_agent_ids:
            dto = ThreadService._fetch_minimal_agent_dto(agent_id.agent_class, agent_id.agent_id, t)
            if dto:
                final_participating_agents.append(dto)

        response.participating_agents = sorted(final_participating_agents, key=lambda a: (a.agent_class, a.agent_id))

        # 6. Calculate overall thread statistics
        overall_stats: CalculatedThreadStats = ThreadService._calculate_overall_thread_stats(
            processed_results.display_aggregates
        )

        # 7. Populate the response DTO with overall statistics
        response.num_events = overall_stats.num_events
        response.num_turns = overall_stats.num_turns
        response.has_pending = overall_stats.has_pending
        response.has_errors = overall_stats.has_errors
        response.is_hitl = overall_stats.is_hitl
        response.open_hitl = overall_stats.open_hitl
        response.is_bitl = overall_stats.is_bitl
        response.open_bitl = overall_stats.open_bitl
        response.is_aitl = overall_stats.is_aitl
        response.open_aitl = overall_stats.open_aitl
        response.llm_cost = overall_stats.llm_cost
        response.first_interaction = overall_stats.first_interaction
        response.latest_interaction = overall_stats.latest_interaction
        response.duration = overall_stats.duration

        return response
