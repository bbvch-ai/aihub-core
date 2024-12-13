import logging
import traceback
from typing import List

from bson import ObjectId
from lib_core.nats.events import ExceptionEvent
from lib_core.nats.topic_managers.TopicManager import TopicManager
from lib_core.nats.topics.agents.AgentTopic import AgentTopic
from lib_core.persistence.messaging.entities.PersistedEventEntity import PersistedEventEntity
from lib_core.persistence.messaging.entities.ThreadEntity import ThreadEntity
from api_core.sockets.events.server_to_user.WSServerEvent import WSServerEvent
from api_core.sockets.events.user_to_server.WSUserEvent import WSUserEvent

logger = logging.getLogger(__name__)

class EventService:

    @staticmethod
    def get_user_events(user_oid: str) -> List[WSServerEvent]:
        """
        Retrieve all events for a given user.
        """
        user_threads = ThreadEntity.get_threads_by_user(user_oid)
        thread_ids = [str(thread.id) for thread in user_threads]
        persisted_events = PersistedEventEntity.display_events_for_threads(thread_ids)
        return [WSServerEvent.from_persisted_event(event) for event in persisted_events]

    @staticmethod
    async def handle_ws_event(
        event: WSUserEvent,
        user_oid: str,
        ws_receiver,
        ws_sender
    ):
        """
        Handle incoming websocket user events. If there's an exception, 
        send back an ExceptionEvent.
        """
        try:
            logger.debug(f"Handling event: {event}")
            await ws_receiver.receive_event(event, user_oid)
        except Exception as e:
            traceback.print_exc()
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
