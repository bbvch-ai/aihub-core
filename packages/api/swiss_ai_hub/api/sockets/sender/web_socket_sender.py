import logging

from cachetools import TTLCache
from swiss_ai_hub.core.events.agent import DisplayEvent
from swiss_ai_hub.core.persistence.messaging.entities.thread_entity import ThreadEntity
from swiss_ai_hub.core.topics.agents import AgentInstanceTopic

from swiss_ai_hub.api.sockets.manager.web_socket_manager import WebSocketManager

logger = logging.getLogger(__name__)

_USERS_IN_THREAD_CACHE: TTLCache = TTLCache(maxsize=128, ttl=60)


class WebSocketSender:
    """
    Responsible for sending relevant DisplayEvents to all users
    associated with a given thread via their active WebSocket connections.

    When an event occurs (e.g., chunks of data from an agent), the front-end connected via WebSockets
    needs to be updated in real time. This class:
    - Looks up the thread to find its associated users.
    - Constructs a ContextualizedAgentEvent from the DisplayEvent.
    - Sends the ContextualizedAgentEvent to each user's WebSocket connection(s).

    This abstraction keeps the pipeline clean: the event handler receives a DisplayEvent, and
    WebSocketSender ensures it reaches every relevant user interface.

    Suppose a user interface is displaying messages from a conversation thread. When new text chunks
    or display events arrive, `WebSocketSender` ensures all connected clients in that thread see them
    immediately.
    """

    def __init__(self, ws_manager: WebSocketManager):
        self.ws_manager = ws_manager

    @staticmethod
    async def get_users_in_thread(thread_id: str) -> list[str]:
        """Retrieves the users associated with a thread ID.

        Cached by hand: cachetools' `cached` decorator would store the coroutine, which can be awaited only once.
        """
        if thread_id in _USERS_IN_THREAD_CACHE:
            return _USERS_IN_THREAD_CACHE[thread_id]
        thread = await ThreadEntity.get_thread_by_id(thread_id)
        users = [user.user_id for user in thread.users]
        _USERS_IN_THREAD_CACHE[thread_id] = users
        return users

    async def send_event(self, event: DisplayEvent, topic: AgentInstanceTopic):
        """
        Given a DisplayEvent and its topic context:
        - Find the thread's users.
        - Convert the event into a ContextualizedAgentEvent.
        - Send the event to each user via WebSocketManager.
        """
        logger.debug(f"Sending event {event.event_name} to thread {topic.thread_id}")
        users = await self.get_users_in_thread(topic.thread_id)
        for user in users:
            await self.ws_manager.send_agent_event(event, topic, user)
