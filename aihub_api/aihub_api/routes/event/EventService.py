import logging
from typing import List, Optional

from aihub_lib.auth.AuthenticatedUser import AuthenticatedUser
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.nats.distributor.events.ExternalAgentEvent import ExternalAgentEvent
from aihub_lib.nats.distributor.ExternalAgentEventDistributor import ExternalAgentEventDistributor
from aihub_lib.nats.events import ExceptionEvent
from aihub_lib.nats.topic_managers.TopicManager import TopicManager
from aihub_lib.nats.topic_managers.agents.AgentTopicManager import AgentTopicManager
from aihub_lib.nats.topics.agents.AgentTopic import AgentTopic
from aihub_lib.persistence.messaging.entities.PersistedEventEntity import PersistedEventEntity, TimeRange
from aihub_lib.persistence.messaging.entities.ThreadEntity import ThreadEntity
from bson import ObjectId
from starlette.websockets import WebSocket, WebSocketDisconnect

from aihub_api.routes.event.dto.EventTimeseries import EventTimeseries
from aihub_api.sockets.events.server_to_user.WSServerEvent import WSServerEvent
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
    - `handle_external_event`: Receives a `ExternalAgentEvent`, processes it, and sends out responses or errors as needed.

    ### Error Handling
    If an exception occurs while handling an external event, an `ExceptionEvent` is sent back through the WebSocket,
    ensuring that clients receive diagnostic feedback rather than silent failures.
    """

    @staticmethod
    def get_user_events(
        user_oid: str,
        locale: Optional[str] = None,
        thread_id: Optional[ObjectId] = None,
        display_id: Optional[ObjectId] = None,
        event_class: Optional[str] = None,
    ) -> List[WSServerEvent]:
        """
        Retrieves all display events for a given user by:
        1. Finding all threads the user is part of.
        2. Querying the persistence layer for display events in those threads.
        3. Converting them into `WSServerEvent`s for consistent client-facing output.
        """
        if thread_id is None:
            user_threads = ThreadEntity.get_threads_by_user(user_oid)
            thread_ids = [str(thread.id) for thread in user_threads]
            persisted_events = PersistedEventEntity.display_events_for_threads(thread_ids, event_name=event_class)
        else:
            persisted_events = PersistedEventEntity.display_events_for_thread(
                thread_id=str(thread_id),
                display_id=str(display_id) if display_id is not None else None,
                event_name=event_class,
            )
        return [WSServerEvent.from_persisted_event(event, locale=locale) for event in persisted_events]

    @staticmethod
    def get_all_thread_display_events(thread_id: str) -> List[PersistedEventEntity]:
        """
        Retrieves all display events for a thread.
        """
        return PersistedEventEntity.display_events_for_thread(thread_id)

    @staticmethod
    async def handle_external_event(
        event: ExternalAgentEvent,
        user: AuthenticatedUser,
        external_event_distributor: ExternalAgentEventDistributor,
        ws_sender: WebSocketSender,
    ):
        """
        Handles a user-sent WebSocket event. Usually, the event instructs the system (e.g., start a new agent run,
        send a message, etc.). If an error occurs, an ExceptionEvent is sent back to the user.
        """
        try:
            logger.debug(f"Handling event: {event}")
            await external_event_distributor.distribute_event(event, user)
        except Exception as e:
            logger.exception(e)
            # If there's an error, notify the user with an ExceptionEvent
            await ws_sender.send_event(
                ExceptionEvent(message=str(e)),
                topic=AgentTopic(
                    agent_class="ExceptionAgent",
                    agent_id=user.oid,
                    run_id=str(ObjectId()),
                    thread_id=event.thread_id,
                    display_id=event.display_id,
                    event_type=AgentTopicManager.DISPLAY_EVENT,
                    event_name=ExceptionEvent.event_name_from_class(),
                    event_id=str(ObjectId()),
                ),
            )

    @staticmethod
    async def event_websocket_connection(
        websocket: WebSocket,
        ws_sender: WebSocketSender,
        ws_manager: WebSocketManager,
        external_event_distributor: ExternalAgentEventDistributor,
        user: AuthenticatedUser,
        t: LocaleHandler,
    ):
        logger.debug(f"User {user.oid} connected to websocket")
        await ws_manager.connect(websocket, user.oid, t.locale)

        # Process incoming messages
        try:
            logger.debug(f"Receiving events for User {user.oid}")
            while True:
                data = await websocket.receive_json()
                logger.debug(f"Received data: {data}")
                event = ExternalAgentEvent.deserialize_event(data)

                # Handle the received event
                await EventService.handle_external_event(event, user, external_event_distributor, ws_sender)

        except WebSocketDisconnect as e:
            logging.error(f"Websocket disconnected: {e}")
            logger.debug(f"User {user.oid} disconnected from websocket")
            await ws_manager.disconnect(websocket, user.oid)

    @staticmethod
    def get_event_timeseries(
        time_range: TimeRange,
        thread_id: Optional[ObjectId] = None,
        agent_id: Optional[ObjectId] = None,
        agent_class: Optional[str] = None,
        event_name: Optional[str] = None,
    ) -> EventTimeseries:
        """Gets time-based statistics for a thread."""
        buckets, start_time, end_time, resolution = PersistedEventEntity.get_event_timeseries(
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
