import logging

from fastapi import WebSocket
from swiss_ai_hub.core.events.agent import DisplayEvent
from swiss_ai_hub.core.i18n import LocaleHandler
from swiss_ai_hub.core.topics.agents import AgentInstanceTopic

from swiss_ai_hub.api.sockets.events.server_to_user.contextualized_agent_event import ContextualizedAgentEvent

logger = logging.getLogger(__name__)


class WebSocketManager:
    """
    Manages active WebSocket connections between the server and users, allowing multiple
    concurrent connections per user and broadcasting events to all of a user's connections.

    In a real-time application, a single user might connect from multiple tabs, browsers,
    or devices simultaneously. `WebSocketManager`:
    - Tracks all active connections for each user.
    - Allows sending events to all of a user’s connected clients without duplicating logic.
    - Cleans up disconnected connections gracefully.

    ### Features
    - **Multiple Connections per User:** Each user_id maps to a set of WebSocket connections.
    - **Broadcasting Events:** `send_event` sends a JSON-serialized event to all the user's
      active connections, ensuring synchronized updates across all their devices/tabs.
    - **Automatic Cleanup:** If sending fails for a connection (e.g., network error), that
      connection is removed.

    ### Workflow
    1. **connect(user_id):** Called when a new WebSocket handshake completes, adding the connection
       to that user's set.
    2. **disconnect(user_id):** Called when a WebSocket closes, removing the connection.
    3. **send_event(user_id):** Sends a given event to all of the user's active connections. If
       any fail, they are removed from the active set.

    ### Example
    ```python
    ws_manager = WebSocketManager()

    # On WebSocket connection
    await ws_manager.connect(websocket, user_id="user123")

    # Later, to send an event
    event = ContextualizedAgentEvent(...)
    await ws_manager.send_event(event, user_id="user123")

    # On disconnection
    await ws_manager.disconnect(websocket, user_id="user123")
    ```
    """

    def __init__(self):
        self.active_connections: dict[str, set[WebSocket]] = {}
        self.user_preferred_locale: dict[str, str] = {}

    async def connect(self, websocket: WebSocket, user_id: str, locale: str) -> None:
        """
        Register a new active connection for the given user.

        If the user has no prior connections, create a new set. Otherwise, add to the existing set.
        """
        logger.debug(f"Connecting user {user_id}")
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)
        self.user_preferred_locale[user_id] = locale

    async def disconnect(self, websocket: WebSocket, user_id: str) -> None:
        """
        Remove a WebSocket connection from the user's set of active connections.

        If that was the user's last active connection, remove the user entry entirely.
        """
        logger.debug(f"Disconnecting user {user_id}")
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

    async def send_agent_event(self, event: DisplayEvent, topic: AgentInstanceTopic, user_id: str) -> None:
        """
        Send a JSON-serialized version of the given event to all active connections of the specified user.

        If sending to a particular connection fails (e.g., due to a network error),
        that connection is removed. If no connections remain for that user, their entry is removed.
        """
        logger.debug(f"Sending event {event.model_dump()} to user {user_id}")
        if user_id in self.active_connections:
            locale = self.user_preferred_locale.get(user_id)
            locale_handler = LocaleHandler(locale=locale)
            contextualized_event = ContextualizedAgentEvent(
                locale=locale or LocaleHandler.DEFAULT_LOCALE,
                agent_class=topic.agent_class,
                agent_id=topic.agent_id,
                thread_id=topic.thread_id,
                display_id=topic.display_id,
                run_id=topic.run_id,
                event_type=topic.event_type,
                event_name=topic.event_name,
                event_id=event.event_id,
                event=event,
                event_display_name=locale_handler.extract(event.display_name),
                event_display_description=locale_handler.extract(event.display_description),
            )
            data = contextualized_event.model_dump()
            for ws in list(self.active_connections[user_id]):
                try:
                    await ws.send_json(data)
                except Exception:
                    logger.warning("Failed to send event to a connection, removing it.")
                    self.active_connections[user_id].discard(ws)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
