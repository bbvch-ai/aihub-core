import logging

from bson import ObjectId
from nats.aio.client import Client as NATS
from nats.js import JetStreamContext

from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.distributor.events.external_agent_event import ExternalAgentEvent
from swiss_ai_hub.core.persistence.messaging.entities.persisted_agent_event_entity import PersistedAgentEventEntity
from swiss_ai_hub.core.persistence.messaging.entities.thread_entity import ThreadEntity
from swiss_ai_hub.core.publishers.js_publisher import JSPublisher
from swiss_ai_hub.core.publishers.nc_publisher import NCPublisher
from swiss_ai_hub.core.topic_managers.agents.agent_thread_topic_manager import AgentThreadTopicManager
from swiss_ai_hub.core.topic_managers.agents.agent_topic_manager import AgentTopicManager

logger = logging.getLogger(__name__)


class ExternalAgentEventDistributor:
    """
    Processes events received from the user via an external system like API, WebSockets or Bots,
    transforming them into NATS/JetStream events that the rest of the system can consume.
    This class essentially bridges user actions back into the event-driven architecture.

    Users might send messages, start commands, or respond to human-in-the-loop prompts.
    The server must:
    - Validate the user's thread membership.
    - Determine the correct agent/topic subjects.
    - Publish the user's event (e.g. a StartEvent or a DisplayEvent) as a JetStream event,
      ensuring downstream agents or services can react.
    """

    def __init__(self, nc: NATS, js: JetStreamContext, name: str = "ExternalAgentEventDistributor"):
        self.nc_publisher = NCPublisher(name, nc)
        self.js_publisher = JSPublisher(name, js)

    async def distribute_event(
        self,
        external_event: ExternalAgentEvent,
        user: UserIdentity | None = None,
        aihub_headers: dict[str, str] | None = None,
    ):
        """
        Entry point for distributing an external event (ExternalAgentEvent) to agents or other systems through NATs.

        Validates user's membership in the thread, identifies the event type, and delegates
        to specialized handlers.

        `aihub_headers` carries X-AIHub-* request headers (e.g. user-identity tokens) on the
        NATS message envelope, not in the event payload. ``NATSMessageHeaders.with_aihub_headers``
        filters to the ``X-AIHub-*`` prefix before publishing, so any non-prefixed header in the
        dict is dropped on its way out.
        """
        thread = ThreadEntity.get_thread_by_id(external_event.thread_id)

        if user:
            user_id = user.id
            logger.debug(f"Received event {external_event.event.event_name} for thread {external_event.thread_id}")
            users_in_thread = [user.user_id for user in thread.users]

            if user_id not in users_in_thread:
                logger.exception(f"User {user_id} is not in thread {external_event.thread_id}")
                raise PermissionError(f"User {user_id} is not in thread {external_event.thread_id}")

        if external_event.event.is_start_event:
            run_id = str(ObjectId())
        elif external_event.event.is_hitl_response_event:
            run_id = external_event.event.request_event.topic.run_id
        elif external_event.event.is_bitl_response_event:
            run_id = external_event.event.request_event.topic.run_id
        else:
            raise ValueError(f"Received event of unhandled type: {external_event.event.event_name}")

        if external_event.event.is_hitl_response_event:
            await self._handle_human_in_the_loop_response(thread, external_event, aihub_headers)

        if external_event.event.is_bitl_response_event:
            await self._handle_human_in_the_loop_response(thread, external_event, aihub_headers)

        # Display the message back to the user who sent it - if it was user-sent
        if external_event.event.is_display_event and user:
            await self._handle_display_message(external_event, run_id, user, aihub_headers)

        if external_event.event.is_start_event:
            await self._handle_start_event(thread, external_event, run_id, aihub_headers)

    async def _handle_start_event(
        self,
        thread: ThreadEntity,
        external_event: ExternalAgentEvent,
        run_id: str,
        aihub_headers: dict[str, str] | None = None,
    ):
        """
        Handle a StartEvent from the user.

        If the event has no initial messages, load message history from persistence.
        Then, publish the StartEvent to all agents in the thread, giving them the full context.
        """
        logger.debug(f"Handling start event for thread {external_event.thread_id}")

        if hasattr(external_event.event, "messages") and len(external_event.event.messages) == 0:
            external_event.event.messages = PersistedAgentEventEntity.to_message_history(str(thread.id))
            logger.debug(f"Assembled message history {external_event.event.messages}")

        for agent in thread.agents:
            event = external_event.event.model_copy(deep=True)
            event.event_id = str(ObjectId())
            topic_manager = AgentThreadTopicManager(
                agent_class=agent.agent_class,
                agent_id=agent.agent_id,
                thread_id=external_event.thread_id,
                display_id=external_event.display_id,
                run_id=run_id,
            )
            subject = topic_manager.get_subject_for_control_event_in_thread(
                event_name=event.event_name,
                event_id=event.event_id,
            )
            await self.js_publisher.publish_event(event, subject, extra_headers=aihub_headers)

    async def _handle_display_message(
        self,
        external_event: ExternalAgentEvent,
        run_id: str,
        user: UserIdentity,
        aihub_headers: dict[str, str] | None = None,
    ):
        """
        Handle a DisplayEvent from the user.

        Convert it into an event published to the appropriate subject,
        representing user-provided display updates or messages.
        """
        logger.debug(f"Handling display event for thread {external_event.thread_id}")
        topic_manager = AgentTopicManager()
        subject = topic_manager.get_subject_for_specific_event_in_agent(
            agent_class="UserAgent",
            agent_id=user.id,
            thread_id=external_event.thread_id,
            display_id=external_event.display_id,
            run_id=run_id,
            event_type=AgentTopicManager.DISPLAY_EVENT,
            event_name=external_event.event.event_name,
            event_id=external_event.event.event_id,
        )
        await self.nc_publisher.publish_event(external_event.event, subject, extra_headers=aihub_headers)

    async def _handle_human_in_the_loop_response(
        self,
        thread: ThreadEntity,
        external_event: ExternalAgentEvent,
        aihub_headers: dict[str, str] | None = None,
    ):
        """
        Handle a HumanInTheLoopResponseEvent.

        Checks that the agent mentioned in the event's topic is part of the thread.
        Then publishes the HITL response to the appropriate subject so the agent can process it.
        """
        logger.debug(f"Handling human in the loop response for thread {external_event.thread_id}")
        topic = external_event.event.request_event.topic

        assert str(thread.id) == topic.thread_id, f"Thread ID mismatch: {thread.id} != {topic.thread_id}"

        topic_manager = AgentThreadTopicManager(
            agent_class=topic.agent_class,
            agent_id=topic.agent_id,
            thread_id=topic.thread_id,
            display_id=topic.display_id,
            run_id=topic.run_id,
        )
        subject = topic_manager.get_subject_for_control_event_in_thread(
            event_name=external_event.event.event_name,
            event_id=external_event.event.event_id,
        )
        await self.js_publisher.publish_event(external_event.event, subject, extra_headers=aihub_headers)
