import logging

from api_core.sockets.events.server_to_user.WSServerEvent import WSServerEvent
from api_core.sockets.manager.WebSocketManager import WebSocketManager
from lib_core.nats.events import DisplayEvent
from lib_core.nats.topics.agents.AgentTopic import AgentTopic
from lib_core.persistence.messaging.entities.ThreadEntity import ThreadEntity

logger = logging.getLogger(__name__)


class WebSocketSender:

    def __init__(self, ws_manager: WebSocketManager):
        self.ws_manager = ws_manager

    async def send_event(self, event: DisplayEvent, topic: AgentTopic):
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
