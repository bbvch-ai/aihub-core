import logging

from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.nats.distributor.events.ExternalAgentEvent import ExternalAgentEvent
from aihub_lib.nats.distributor.ExternalAgentEventDistributor import ExternalAgentEventDistributor
from aihub_lib.nats.events import ExceptionEvent
from aihub_lib.nats.topic_managers.agents.AgentTopicManager import AgentTopicManager
from aihub_lib.nats.topics.agents.AgentTopic import AgentTopic
from aihub_lib.persistence.messaging.entities.PersistedAgentEventEntity import PersistedAgentEventEntity, TimeRange
from bson import ObjectId
from starlette.websockets import WebSocket, WebSocketDisconnect

from aihub_api.routes.event.dto.EventTimeseries import EventTimeseries
from aihub_api.sockets.events.server_to_user.WSServerAgentEvent import WSServerAgentEvent
from aihub_api.sockets.manager.WebSocketManager import WebSocketManager
from aihub_api.sockets.sender.WebSocketSender import WebSocketSender

logger = logging.getLogger(__name__)


class EventService:
    """
    Provides business logic for event-related operations:
    - Fetching persisted events for a user.
    - Handling incoming user-sent events on the WebSocket and routing them to appropriate handlers.

    ### Why EventService?
    By isolating event logic in a service, the controller remains clean and easy to maintain.
    The service deals with:
    - Database retrieval of persisted events.
    - Handling user commands/events and relaying them to the correct subsystem (via ExternalAgentEventDistributor).
    - Sending errors back to the user if something goes wrong.

    ### Key Operations
    - `get_user_events`: Returns all events relevant to a user’s threads.
    - `handle_external_event`: Receives a `ExternalAgentEvent`, processes it, and sends out responses or
       errors as needed.

    ### Error Handling
    If an exception occurs while handling an external event, an `ExceptionEvent` is sent back through the WebSocket,
    ensuring that clients receive diagnostic feedback rather than silent failures.
    """

    @staticmethod
    def get_events_in_thread(
        thread_id: ObjectId,
        locale: str | None = None,
        display_id: ObjectId | None = None,
        event_class: str | None = None,
    ) -> list[WSServerAgentEvent]:
        """
        Retrieves all display events for a given user by:
        1. Finding all threads the user is part of.
        2. Querying the persistence layer for display events in those threads.
        3. Converting them into `WSServerAgentEvent`s for consistent client-facing output.
        """
        persisted_events = PersistedAgentEventEntity.display_events_for_thread(
            thread_id=str(thread_id),
            display_id=str(display_id) if display_id is not None else None,
            event_name=event_class,
        )
        return [WSServerAgentEvent.from_persisted_event(event, locale=locale) for event in persisted_events]

    @staticmethod
    def get_all_thread_display_events(thread_id: str) -> list[PersistedAgentEventEntity]:
        """
        Retrieves all display events for a thread.
        """
        return PersistedAgentEventEntity.display_events_for_thread(thread_id)

    @staticmethod
    async def event_websocket_connection(
        websocket: WebSocket,
        ws_manager: WebSocketManager,
        user: UserIdentity,
        t: LocaleHandler,
    ):
        logger.debug(f"User {user.id} connected to websocket")
        await ws_manager.connect(websocket, user.id, t.locale)

        # Process incoming messages
        try:
            logger.debug(f"Receiving events for User {user.id}")
            while True:
                data = await websocket.receive_json()
                logger.debug(f"Received data: {data}")

        except WebSocketDisconnect as e:
            logging.error(f"Websocket disconnected: {e}")
            logger.debug(f"User {user.id} disconnected from websocket")
            await ws_manager.disconnect(websocket, user.id)


    @staticmethod
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
            agent_id=agent_id,
            agent_class=agent_class,
            event_name=event_name,
            thread_id=thread_id,
            time_range=time_range,
            resolution=resolution,
            start_time=start_time,
            end_time=end_time,
            buckets=buckets,
        )
