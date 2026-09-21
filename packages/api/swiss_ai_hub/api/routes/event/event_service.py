import asyncio
import logging
from datetime import datetime

from bson import ObjectId
from starlette.websockets import WebSocket, WebSocketDisconnect
from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.i18n import LocaleHandler
from swiss_ai_hub.core.infrastructure import trace_fn
from swiss_ai_hub.core.persistence import LLMSpend
from swiss_ai_hub.core.persistence.messaging.entities.persisted_agent_event_entity import (
    PersistedAgentEventEntity,
    TimeRange,
)

from swiss_ai_hub.api.routes.event.dto.event_timeseries import EventTimeseries
from swiss_ai_hub.api.sockets.events.server_to_user.contextualized_agent_event import ContextualizedAgentEvent
from swiss_ai_hub.api.sockets.manager.web_socket_manager import WebSocketManager

logger = logging.getLogger(__name__)


class EventService:
    """
    Provides business logic for event-related operations:
    - Fetching persisted events for a user.
    - Handling incoming user-sent events on the WebSocket and routing them to appropriate handlers.

    By isolating event logic in a service, the controller remains clean and easy to maintain.
    The service deals with:
    - Database retrieval of persisted events.
    - Handling user commands/events and relaying them to the correct subsystem (via ExternalAgentEventDistributor).
    - Sending errors back to the user if something goes wrong.
    """

    @staticmethod
    @trace_fn
    def get_events_in_thread(
        thread_id: ObjectId,
        locale: str | None = None,
        display_id: ObjectId | None = None,
        event_class: str | None = None,
    ) -> list[ContextualizedAgentEvent]:
        """Retrieves all display events for a given user."""
        persisted_events = PersistedAgentEventEntity.display_events_for_thread(
            thread_id=str(thread_id),
            display_id=str(display_id) if display_id is not None else None,
            event_name=event_class,
        )
        return [ContextualizedAgentEvent.from_persisted_event(event, locale=locale) for event in persisted_events]

    @staticmethod
    @trace_fn
    def thread_id_for_display(display_id: str) -> str | None:
        """Resolve the thread that owns a display, so the chat-UI side panel can open the correct per-agent thread
        without recomputing the salted thread_id."""
        return PersistedAgentEventEntity.thread_id_for_display(display_id)

    @staticmethod
    @trace_fn
    def get_all_thread_display_events(thread_id: str) -> list[PersistedAgentEventEntity]:
        """Retrieves all display events for a thread."""
        return PersistedAgentEventEntity.display_events_for_thread(thread_id)

    @staticmethod
    @trace_fn
    async def event_websocket_connection(
        websocket: WebSocket,
        ws_manager: WebSocketManager,
        user: UserIdentity,
        t: LocaleHandler,
    ):
        logger.debug(f"User {user.id} connected to websocket")
        await ws_manager.connect(websocket, user.id, t.locale)

        try:
            logger.debug(f"Receiving events for User {user.id}")
            while True:
                data = await websocket.receive_json()
                logger.warning(f"Received data through websocket connection, but it will be ignored: {data}")

        except WebSocketDisconnect as e:
            logging.exception(f"Websocket disconnected: {e}")
            logger.debug(f"User {user.id} disconnected from websocket")
            await ws_manager.disconnect(websocket, user.id)

    @staticmethod
    @trace_fn
    def get_event_timeseries(
        time_range: TimeRange,
        thread_id: ObjectId | None = None,
        agent_id: ObjectId | None = None,
        agent_class: str | None = None,
        event_name: str | None = None,
    ) -> EventTimeseries:
        """Gets time-based statistics for a thread."""
        buckets, start_time, end_time, resolution = PersistedAgentEventEntity.get_event_timeseries(
            time_range=time_range,
            agent_id=agent_id,
            agent_class=agent_class,
            event_name=event_name,
            thread_id=thread_id,
        )

        return EventTimeseries(
            agent_id=str(agent_id) if agent_id else None,
            agent_class=agent_class,
            event_name=event_name,
            thread_id=str(thread_id) if thread_id else None,
            time_range=time_range,
            resolution=resolution,
            start_time=start_time,
            end_time=end_time,
            buckets=buckets,
        )

    @staticmethod
    @trace_fn
    async def get_llm_spend_by_user(tenant_id: str | None = None, since: datetime | None = None) -> list[LLMSpend]:
        """LLM spend per user, narrowed to one tenant unless the caller may see the whole platform.

        Off the event loop, because the aggregation is synchronous and its runtime grows with the
        window: measured at 123s on staging for a cold 30-day window, which froze every other
        request — including the health probe, whose three failures then had Docker call the whole
        container unhealthy and gunicorn kill the worker."""
        return await asyncio.to_thread(
            PersistedAgentEventEntity.get_llm_spend_by_user, tenant_id=tenant_id, since=since
        )

    @staticmethod
    @trace_fn
    async def get_llm_spend_by_tenant(since: datetime | None = None) -> list[LLMSpend]:
        """LLM spend per tenant across the platform. Off the event loop — see `get_llm_spend_by_user`."""
        return await asyncio.to_thread(PersistedAgentEventEntity.get_llm_spend_by_tenant, since=since)
