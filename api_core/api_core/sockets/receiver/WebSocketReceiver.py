import logging

from bson import ObjectId
from nats.js import JetStreamContext

from api_core.sockets.events.user_to_server.WSUserEvent import WSUserEvent
from lib_core.nats.events import DisplayEvent, StartEvent
from lib_core.nats.events.human_in_the_loop import HumanInTheLoopResponseEvent
from lib_core.nats.publishers.JSPublisher import JSPublisher
from lib_core.nats.topic_managers.TopicManager import TopicManager
from lib_core.nats.topic_managers.agents.AgentThreadTopicManager import AgentThreadTopicManager
from lib_core.persistence.messaging.entities.PersistedEventEntity import PersistedEventEntity
from lib_core.persistence.messaging.entities.ThreadEntity import ThreadEntity

logger = logging.getLogger(__name__)


class WebSocketReceiver:

    def __init__(self, js: JetStreamContext):
        self.publisher = JSPublisher(js)

    async def receive_event(self, ws_vent: WSUserEvent, user_id: str):
        thread = ThreadEntity.get_thread_by_id(ws_vent.thread_id)
        logger.debug(f"Received event {ws_vent.event.__class__.__name__} for thread {ws_vent.thread_id}")
        users_in_thread = [user.user_id for user in thread.users]

        if user_id not in users_in_thread:
            logger.error(f"User {user_id} is not in thread {ws_vent.thread_id}")
            raise Exception(f"User {user_id} is not in thread {ws_vent.thread_id}")

        if isinstance(ws_vent.event, HumanInTheLoopResponseEvent):
            run_id = ws_vent.event.request_event.topic.run_id
            await self._handle_human_in_the_loop_response(thread, ws_vent)
        else:
            run_id = str(ObjectId())

        if isinstance(ws_vent.event, DisplayEvent):
            await self._handle_display_message(ws_vent, run_id, user_id)

        if isinstance(ws_vent.event, StartEvent):
            await self._handle_start_event(thread, ws_vent, run_id)

    async def _handle_start_event(self, thread: ThreadEntity, ws_event: WSUserEvent, run_id: str):
        logger.debug(f"Handling start event for thread {ws_event.thread_id}")

        if len(ws_event.event.messages) == 0:
            ws_event.event.messages = PersistedEventEntity.to_message_history(str(thread.id))
            logger.debug(f"Assembled message history {ws_event.event.messages}")

        for agent in thread.agents:
            topic_manager = AgentThreadTopicManager(
                agent_class=agent.agent_class,
                agent_id=agent.agent_id,
                thread_id=ws_event.thread_id,
                display_id=ws_event.display_id,
                run_id=run_id,
            )
            subject = topic_manager.get_subject_for_control_event_in_thread(
                event_name=ws_event.event.__class__.__name__
            )
            await self.publisher.publish_event(ws_event.event, subject)

    async def _handle_display_message(self, ws_event: WSUserEvent, run_id: str, user_id: str):
        logger.debug(f"Handling display event for thread {ws_event.thread_id}")
        topic_manager = TopicManager()
        subject = topic_manager.get_subject_for_specific_event_in_agent(
            agent_class="UserAgent",
            agent_id=user_id,
            thread_id=ws_event.thread_id,
            display_id=ws_event.display_id,
            run_id=run_id,
            event_type=TopicManager.DISPLAY_EVENT,
            event_name=ws_event.event.__class__.__name__,
        )
        await self.publisher.publish_event(ws_event.event, subject)

    async def _handle_human_in_the_loop_response(self, thread: ThreadEntity, ws_event: WSUserEvent):
        logger.debug(f"Handling human in the loop response for thread {ws_event.thread_id}")
        topic = ws_event.event.request_event.topic

        assert str(thread.id) == topic.thread_id, f"Thread ID mismatch: {thread.id} != {topic.thread_id}"

        # Assert agent is in thread
        for agent in thread.agents:
            if agent.agent_id == topic.agent_id and agent.agent_class == topic.agent_class:
                break
        else:
            raise Exception(
                f"Agent {topic.agent_id} of class {topic.agent_class} is not in thread {topic.thread_id}")

        topic_manager = AgentThreadTopicManager(
            agent_class=topic.agent_class,
            agent_id=topic.agent_id,
            thread_id=topic.thread_id,
            display_id=topic.display_id,
            run_id=topic.run_id,
        )
        subject = topic_manager.get_subject_for_control_event_in_thread(
            event_name=ws_event.event.__class__.__name__
        )
        await self.publisher.publish_event(ws_event.event, subject)
