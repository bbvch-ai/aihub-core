import logging
import traceback
from typing import List

from bson import ObjectId

from aihub_api.sockets.receiver.WebSocketReceiver import WebSocketReceiver
from aihub_api.sockets.sender.WebSocketSender import WebSocketSender
from aihub_lib.nats.events import ExceptionEvent
from aihub_lib.nats.topic_managers.TopicManager import TopicManager
from aihub_lib.nats.topics.agents.AgentTopic import AgentTopic
from aihub_lib.persistence.messaging.entities.PersistedEventEntity import PersistedEventEntity
from aihub_lib.persistence.messaging.entities.ThreadEntity import ThreadEntity
from aihub_api.sockets.events.server_to_user.WSServerEvent import WSServerEvent
from aihub_api.sockets.events.user_to_server.WSUserEvent import WSUserEvent

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
    - Handling user commands/events and relaying them to the correct subsystem (via WebSocketReceiver).
    - Sending errors back to the user if something goes wrong.

    ### Key Operations
    - `get_user_events`: Returns all events relevant to a user’s threads.
    - `handle_ws_event`: Receives a `WSUserEvent`, processes it, and sends out responses or errors as needed.

    ### Error Handling
    If an exception occurs while handling a user event, an `ExceptionEvent` is sent back through the WebSocket,
    ensuring that clients receive diagnostic feedback rather than silent failures.
    """

    @staticmethod
    def get_user_events(user_oid: str) -> List[WSServerEvent]:
        """
        Retrieves all events for a given user by:
        1. Finding all threads the user is part of.
        2. Querying the persistence layer for display events in those threads.
        3. Converting them into `WSServerEvent`s for consistent client-facing output.
        """
        user_threads = ThreadEntity.get_threads_by_user(user_oid)
        thread_ids = [str(thread.id) for thread in user_threads]
        persisted_events = PersistedEventEntity.display_events_for_threads(thread_ids)
        return [WSServerEvent.from_persisted_event(event) for event in persisted_events]

    @staticmethod
    async def handle_ws_event(
        event: WSUserEvent,
        user_oid: str,
        ws_receiver: WebSocketReceiver,
        ws_sender: WebSocketSender,
    ):
        """
        Handles a user-sent WebSocket event. Usually, the event instructs the system (e.g., start a new agent run,
        send a message, etc.). If an error occurs, an ExceptionEvent is sent back to the user.
        """
        try:
            logger.debug(f"Handling event: {event}")
            await ws_receiver.receive_event(event, user_oid)
        except Exception as e:
            traceback.print_exc()
            # If there's an error, notify the user with an ExceptionEvent
            await ws_sender.send_event(
                ExceptionEvent(message=str(e)),
                topic=AgentTopic(
                    agent_class="ExceptionAgent",
                    agent_id=user_oid,
                    run_id=str(ObjectId()),
                    thread_id=event.thread_id,
                    display_id=event.display_id,
                    event_type=TopicManager.DISPLAY_EVENT,
                    event_name=ExceptionEvent.__name__,
                    event_id=str(ObjectId()),
                ),
            )
