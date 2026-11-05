import asyncio
import logging

from cachetools import TTLCache
from swiss_ai_hub.core.events.agent import DisplayEvent
from swiss_ai_hub.core.persistence.messaging.entities.thread_entity import ThreadEntity
from swiss_ai_hub.core.topics.agents import AgentInstanceTopic

from swiss_ai_hub.api.sockets.manager.web_socket_manager import WebSocketManager

logger = logging.getLogger(__name__)

_USERS_IN_THREAD_CACHE: TTLCache[str, asyncio.Task[list[str]]] = TTLCache(maxsize=128, ttl=60)


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

        Caches the lookup task rather than its result: each display event is handled in its own task, and caching only
        the result let every event of a burst miss the cache while the first lookup was still waiting.
        """
        lookup = _USERS_IN_THREAD_CACHE.get(thread_id)
        if lookup is None:
            lookup = asyncio.create_task(WebSocketSender._load_users_in_thread(thread_id))
            lookup.add_done_callback(lambda done: WebSocketSender._forget_failed_lookup(thread_id, done))
            _USERS_IN_THREAD_CACHE[thread_id] = lookup
        # Shielded: one cancelled event handler must not cancel the lookup that the other events are waiting for.
        return await asyncio.shield(lookup)

    @staticmethod
    async def _load_users_in_thread(thread_id: str) -> list[str]:
        thread = await ThreadEntity.get_thread_by_id(thread_id)
        return [user.user_id for user in thread.users]

    @staticmethod
    def _forget_failed_lookup(thread_id: str, done: asyncio.Task[list[str]]) -> None:
        """Drops a cancelled or failed lookup, so a later event retries it instead of inheriting the failure."""
        if (done.cancelled() or done.exception() is not None) and _USERS_IN_THREAD_CACHE.get(thread_id) is done:
            del _USERS_IN_THREAD_CACHE[thread_id]

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
