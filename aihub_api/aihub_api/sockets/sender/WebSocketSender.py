import logging

from aihub_lib.nats.events import DisplayEvent
from aihub_lib.nats.topics.agents.AgentTopic import AgentTopic
from aihub_lib.persistence.messaging.entities.ThreadEntity import ThreadEntity

from aihub_api.sockets.events.server_to_user.WSServerEvent import WSServerEvent
from aihub_api.sockets.manager.WebSocketManager import WebSocketManager

logger = logging.getLogger(__name__)


class WebSocketSender:
    """
    Responsible for converting DisplayEvents into WSServerEvents and sending them to all users
    associated with a given thread via their active WebSocket connections.

    ### Why WebSocketSender?
    When an event occurs (e.g., chunks of data from an agent), the front-end connected via WebSockets
    needs to be updated in real time. This class:
    - Looks up the thread to find its associated users.
    - Constructs a WSServerEvent from the DisplayEvent.
    - Sends the WSServerEvent to each user's WebSocket connection(s).

    This abstraction keeps the pipeline clean: the event handler receives a DisplayEvent, and
    WebSocketSender ensures it reaches every relevant user interface.

    ### Flow
    1. `send_event` is called with a DisplayEvent and its AgentTopic context.
    2. The method retrieves the ThreadEntity and enumerates all users in that thread.
    3. For each user, the event is turned into a WSServerEvent and sent via WebSocketManager.

    ### Example
    Suppose a user interface is displaying messages from a conversation thread. When new text chunks
    or display events arrive, `WebSocketSender` ensures all connected clients in that thread see them
    immediately.
    """

    def __init__(self, ws_manager: WebSocketManager):
        self.ws_manager = ws_manager

    async def send_event(self, event: DisplayEvent, topic: AgentTopic):
        """
        Given a DisplayEvent and its topic context:
        - Find the thread's users.
        - Convert the event into a WSServerEvent.
        - Send the event to each user via WebSocketManager.
        """
        logger.debug(f"Sending event {event} to thread {topic.thread_id}")
        thread = ThreadEntity.get_thread_by_id(topic.thread_id)
        users = thread.users
        ws_event = WSServerEvent(
            agent_class=topic.agent_class,
            agent_id=topic.agent_id,
            thread_id=topic.thread_id,
            display_id=topic.display_id,
            run_id=topic.run_id,
            event_type=topic.event_type,
            event_name=topic.event_name,
            event_id=event.event_id,
            event_data=event.model_dump(),
        )
        for user in users:
            await self.ws_manager.send_event(ws_event, user.user_id)
