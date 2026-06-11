import asyncio
import logging
from datetime import UTC, datetime

from bson import ObjectId
from cachetools import TTLCache, cached
from fastapi import HTTPException
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
from swiss_ai_hub.core.persistence.messaging.entities.types.thread_sort import SortOrder
from swiss_ai_hub.core.auth.access.access_checker import AccessChecker
from swiss_ai_hub.core.auth.identity.tenant_identity import TenantIdentity
from swiss_ai_hub.core.auth.keycloak.keycloak_admin_service import KeycloakAdminService
from swiss_ai_hub.core.auth.realm_roles import SYS_ADMIN_ROLE
from swiss_ai_hub.core.events import BaseEvent
from swiss_ai_hub.core.events.agent import HumanInTheLoopRequestEvent, HumanInTheLoopResponseEvent
from swiss_ai_hub.core.i18n import LocaleHandler
from swiss_ai_hub.core.infrastructure import trace_fn
from swiss_ai_hub.core.persistence.access.entities.role_entity import RoleEntity
from swiss_ai_hub.core.persistence.access.entities.user_tenant_role_entity import UserTenantRoleEntity
from swiss_ai_hub.core.persistence.messaging.entities.persisted_agent_event_entity import PersistedAgentEventEntity
from swiss_ai_hub.core.persistence.messaging.entities.thread_entity import AgentInstanceRef, ThreadEntity, User
from swiss_ai_hub.core.persistence.messaging.entities.types.thread_filters import ThreadFilters

from swiss_ai_hub.api.routes.agent.dto.agent_identifier import AgentIdentifier
from swiss_ai_hub.api.routes.agent.dto.minimal_agent_instance_dto import MinimalAgentInstanceDTO
from swiss_ai_hub.api.routes.event.event_service import EventService
from swiss_ai_hub.api.routes.openai.dto.history_response import HistoryResponse
from swiss_ai_hub.api.routes.thread.dto.open_chat_hitl_response import OpenChatHitlResponse
from swiss_ai_hub.api.routes.thread.dto.statistics.calculated_thread_stats import CalculatedThreadStats
from swiss_ai_hub.api.routes.thread.dto.statistics.display_statistics import DisplayStatistics
from swiss_ai_hub.api.routes.thread.dto.statistics.intermediate_display_stats import IntermediateDisplayStats
from swiss_ai_hub.api.routes.thread.dto.statistics.processed_run_results import ProcessedRunResults
from swiss_ai_hub.api.routes.thread.dto.statistics.run_statistics import RunStatistics
from swiss_ai_hub.api.routes.thread.dto.thread_agent_dto import ThreadAgentDTO
from swiss_ai_hub.api.routes.thread.dto.thread_dto import ThreadDTO
from swiss_ai_hub.api.routes.user.dto.minimal_user_dto import MinimalUserDTO
from swiss_ai_hub.api.routes.user.user_service import UserService
from swiss_ai_hub.api.sockets.events.server_to_user.contextualized_agent_event import ContextualizedAgentEvent

logger = logging.getLogger(__name__)


class ThreadService:
    """
    A service layer that handles business logic for thread operations.
    """

    @staticmethod
    async def validate_users_have_agent_access(
        user_ids: list[str],
        agents: list[tuple[str, str]],
        tenant: TenantIdentity,
    ) -> None:
        sys_admin_ids = await KeycloakAdminService.get_user_ids_with_realm_role(SYS_ADMIN_ROLE)
        for user_id in user_ids:
            if not await KeycloakAdminService.is_user_member_of_tenant(user_id, tenant.id):
                raise HTTPException(status_code=404, detail=f"User {user_id} not found in tenant")

            user_roles = UserTenantRoleEntity.get_roles_for_user_in_tenant(user_id, tenant.id)
            access_rules = RoleEntity.get_access_rules_for_roles(user_roles, tenant.id)
            access_checker = AccessChecker(
                list(access_rules),
                tenant_access_rules=tenant.access_rules,
                is_sys_admin=user_id in sys_admin_ids,
            )

            for agent_class, agent_id in agents:
                if not access_checker.has_access_to_agent(agent_class, agent_id):
                    raise HTTPException(
                        status_code=403,
                        detail=f"User {user_id} does not have access to agent {agent_class}:{agent_id}",
                    )

    @staticmethod
    @trace_fn
    async def create_thread(
        name: str,
        user_ids: list[str],
        t: LocaleHandler,
        agent_dtos: list[ThreadAgentDTO] | None = None,
    ) -> ThreadDTO:
        users = [User(user_id=user_id) for user_id in user_ids]
        agents = [
            AgentInstanceRef(agent_id=agent.agent_id, agent_class=agent.agent_class) for agent in (agent_dtos or [])
        ]
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
        sort_by: str = "created_at",
        sort_order: SortOrder = SortOrder.DESCENDING,
        search: str | None = None,
        agent_id: str | None = None,
        user_search_id: str | None = None,
        status: str | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> tuple[int, list[ThreadDTO]]:
        """Returns a paginated list of threads that the user is a member of."""
        skip = (page - 1) * page_size
        status_thread_ids = None
        if status:
            user_thread_ids = ThreadEntity.get_thread_ids_for_user(user_id)
            status_thread_ids = PersistedAgentEventEntity.thread_ids_by_status(status, thread_ids=user_thread_ids)
            if not status_thread_ids:
                return 0, []

        filters = ThreadFilters(
            search=search,
            agent_id=agent_id,
            user_search_id=user_search_id,
            status_thread_ids=status_thread_ids,
            from_date=from_date,
            to_date=to_date,
        )

        total = ThreadEntity.count_threads_by_user(user_id, filters=filters)
        threads = ThreadEntity.get_paginated_threads_by_user(
            user_id, skip=skip, limit=page_size, sort_by=sort_by, sort_order=sort_order, filters=filters
        )
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
        agent = AgentInstanceRef(agent_id=agent_id, agent_class=agent_class)
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

        hitl_requests = [HumanInTheLoopRequestEvent.deserialize_event(e.event_data) for e in hitl_request_entities]
        hitl_responses = [HumanInTheLoopResponseEvent.deserialize_event(e.event_data) for e in hitl_response_entities]

        responded_request_ids: set[str] = {response.request_event.event_id for response in hitl_responses}

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
    def _fetch_minimal_agent_dto(agent_class: str, agent_id: str, t: LocaleHandler) -> MinimalAgentInstanceDTO | None:
        """
        Fetches agent details and converts to MinimalAgentInstanceDTO.
        Returns None if the agent cannot be found or fetching fails.
        """
        try:
            from swiss_ai_hub.api.routes.agent.agent_service import AgentService

            return AgentService.get_minimal_agent_instance(agent_class, agent_id, t)
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

            if display_id not in results.display_aggregates:
                results.display_aggregates[display_id] = IntermediateDisplayStats(display_id=display_id)
            display_agg = results.display_aggregates[display_id]

            display_agg.update_from_run_data(run_data)

            # Attempt to fetch the agent that started the run using the cached method
            start_agent_class = run_data.get("start_agent_class")
            start_agent_id = run_data.get("start_agent_id")
            run_agent_dto = ThreadService._fetch_minimal_agent_dto(start_agent_class, start_agent_id, t)

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
        initial_agent_dtos: list[MinimalAgentInstanceDTO] = []
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
        final_participating_agents: list[MinimalAgentInstanceDTO] = []
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
