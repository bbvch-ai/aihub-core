import logging

from bson import ObjectId
from nats.js import JetStreamContext

from aihub_lib.nats.events import DisplayEvent, StartEvent
from aihub_lib.nats.events.human_in_the_loop import HumanInTheLoopResponseEvent
from aihub_lib.nats.publishers.JSPublisher import JSPublisher
from aihub_lib.nats.topic_managers.agents.AgentThreadTopicManager import AgentThreadTopicManager
from aihub_lib.nats.topic_managers.TopicManager import TopicManager
from aihub_lib.persistence.messaging.entities.PersistedEventEntity import PersistedEventEntity
from aihub_lib.persistence.messaging.entities.ThreadEntity import ThreadEntity
from aihub_lib.sockets.events.user_to_server.WSUserEvent import WSUserEvent

logger = logging.getLogger(__name__)


class WebSocketReceiver:
    """
    Processes events received from the user via WebSockets, transforming them into NATS/JetStream
    events that the rest of the system can consume. This class essentially bridges user actions
    back into the event-driven architecture.

    ### Why WebSocketReceiver?
    Users might send messages, start commands, or respond to human-in-the-loop prompts via WebSockets.
    The server must:
    - Validate the user's thread membership.
    - Determine the correct agent/topic subjects.
    - Publish the user's event (e.g. a StartEvent or a DisplayEvent) as a JetStream event,
      ensuring downstream agents or services can react.

    ### Key Responsibilities
    - Validate the user belongs to the thread specified by the event.
    - If it's a `HumanInTheLoopResponseEvent`, ensure the targeted agent belongs to the thread.
    - Publish events to the correct subject derived from the agent/thread IDs.
    - For `StartEvent`s, if no initial messages are provided, fetch the message history and embed it.

    ### Flow
    1. `receive_event`: Main entry point. Identifies the event type and dispatches to the appropriate handler.
    2. `_handle_start_event`: If user starts something (like an agent run), it may reconstruct message history and publish a start event.
    3. `_handle_display_message`: Convert a user-provided `DisplayEvent` into a JetStream event.
    4. `_handle_human_in_the_loop_response`: Ensure correctness and publish the HITL response event.

    ### Example
    Suppose the user sends a message from the frontend UI. The frontend dispatches a `WSUserEvent` to the server.
    `WebSocketReceiver` then:
    - Verifies the user is in the thread.
    - If it's a display event, publishes it so other agents or components can see the user input.
    - If it's a start event, publishes a start event to trigger agent processing.
    """

    def __init__(self, js: JetStreamContext):
        self.publisher = JSPublisher(js)

    async def receive_event(self, ws_event: WSUserEvent, user_id: str):
        """
        Entry point for receiving a user event (WSUserEvent) from the WebSocket layer.

        Validates user's membership in the thread, identifies the event type, and delegates
        to specialized handlers.
        """
        thread = ThreadEntity.get_thread_by_id(ws_event.thread_id)
        logger.debug(f"Received event {ws_event.event.__class__.__name__} for thread {ws_event.thread_id}")
        users_in_thread = [user.user_id for user in thread.users]

        if user_id not in users_in_thread:
            logger.error(f"User {user_id} is not in thread {ws_event.thread_id}")
            raise Exception(f"User {user_id} is not in thread {ws_event.thread_id}")

        if isinstance(ws_event.event, HumanInTheLoopResponseEvent):
            run_id = ws_event.event.request_event.topic.run_id
            await self._handle_human_in_the_loop_response(thread, ws_event)
        else:
            run_id = str(ObjectId())

        if isinstance(ws_event.event, DisplayEvent):
            await self._handle_display_message(ws_event, run_id, user_id)

        if isinstance(ws_event.event, StartEvent):
            await self._handle_start_event(thread, ws_event, run_id)

    async def _handle_start_event(self, thread: ThreadEntity, ws_event: WSUserEvent, run_id: str):
        """
        Handle a StartEvent from the user.

        If the event has no initial messages, load message history from persistence.
        Then, publish the StartEvent to all agents in the thread, giving them the full context.
        """
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
                event_name=ws_event.event.__class__.__name__,
                event_id=ws_event.event.event_id,
            )
            await self.publisher.publish_event(ws_event.event, subject)

    async def _handle_display_message(self, ws_event: WSUserEvent, run_id: str, user_id: str):
        """
        Handle a DisplayEvent from the user.

        Convert it into an event published to the appropriate subject,
        representing user-provided display updates or messages.
        """
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
            event_id=ws_event.event.event_id,
        )
        await self.publisher.publish_event(ws_event.event, subject)

    async def _handle_human_in_the_loop_response(self, thread: ThreadEntity, ws_event: WSUserEvent):
        """
        Handle a HumanInTheLoopResponseEvent.

        Checks that the agent mentioned in the event's topic is part of the thread.
        Then publishes the HITL response to the appropriate subject so the agent can process it.
        """
        logger.debug(f"Handling human in the loop response for thread {ws_event.thread_id}")
        topic = ws_event.event.request_event.topic

        assert str(thread.id) == topic.thread_id, f"Thread ID mismatch: {thread.id} != {topic.thread_id}"

        # Check if agent is in the thread
        for agent in thread.agents:
            if agent.agent_id == topic.agent_id and agent.agent_class == topic.agent_class:
                break
        else:
            raise Exception(f"Agent {topic.agent_id} of class {topic.agent_class} is not in thread {topic.thread_id}")

        topic_manager = AgentThreadTopicManager(
            agent_class=topic.agent_class,
            agent_id=topic.agent_id,
            thread_id=topic.thread_id,
            display_id=topic.display_id,
            run_id=topic.run_id,
        )
        subject = topic_manager.get_subject_for_control_event_in_thread(
            event_name=ws_event.event.__class__.__name__,
            event_id=ws_event.event.event_id,
        )
        await self.publisher.publish_event(ws_event.event, subject)
