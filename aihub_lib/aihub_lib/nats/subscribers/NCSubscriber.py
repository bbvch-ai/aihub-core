import asyncio
import logging
import traceback
from typing import Awaitable, Callable, Generic, Optional, Type, TypeVar

from nats.aio.client import Client as NATS
from nats.aio.msg import Msg
from nats.aio.subscription import Subscription
from nats.errors import BadSubscriptionError, ConnectionDrainingError

from aihub_lib.nats.events import BaseEvent, ControlEvent, DisplayEvent
from aihub_lib.nats.topic_managers.agents.AgentThreadTopicManager import AgentThreadTopicManager
from aihub_lib.nats.topic_managers.TopicManager import TopicManager
from aihub_lib.nats.topics import Topic

logger = logging.getLogger(__name__)

TEvent = TypeVar("TEvent", bound=BaseEvent)


class NCSubscriber(Generic[TEvent]):
    """
    A generic NATS subscriber that reads messages from a given subject and delegates handling
    to a provided async callback. It deserializes event data into a specified event class (TEvent)
    and also parses the message subject into a Topic object for further context.

    ### Why NCSubscriber?
    In an event-driven architecture, you often subscribe to subjects and process incoming messages.
    By standardizing subscription logic (e.g., handling unsubscribes, parsing topics, deserializing events),
    NCSubscriber simplifies consumers and ensures consistent error handling and logging.

    ### Key Features
    - **Generic Event Handling:** You provide a TEvent type, and the subscriber automatically
      deserializes the data according to that event type.
    - **Topic Parsing:** The subscriber uses `Topic.from_subject` to transform the subject into a
      structured Topic object, making it easy for handlers to understand the origin and scope of the event.
    - **Lifecycle Management:** `start()` and `stop()` methods manage the subscription lifecycle,
      including safe unsubscription.

    ### Example
    Create a subscriber that listens to all display events for a given agent, providing a handler
    function that updates a UI or logs the events.
    """

    def __init__(
        self,
        nc: NATS,
        subject: str,
        event_cls: Type[TEvent],
        handler: Callable[[TEvent, Topic], Awaitable[None]],
    ):
        self.nc = nc
        self.subject = subject
        self.subscription: Optional[Subscription] = None
        self.event_cls = event_cls
        self.handler = handler

    async def start(self) -> None:
        """Subscribe to the configured subject and begin receiving messages."""
        self.subscription = await self.nc.subscribe(self.subject, cb=self.message_handler)
        logger.debug(f"Subscribed to '{self.subject}'.")

    async def stop(self) -> None:
        """Unsubscribe from the subject, stopping incoming messages."""
        if self.subscription:
            try:
                await self.subscription.unsubscribe()
                logger.debug(f"Unsubscribed from '{self.subject}'.")
            except (BadSubscriptionError, ConnectionDrainingError):
                logger.debug(f"Subscription '{self.subject}' was already unsubscribed.")

    async def message_handler(self, msg: Msg) -> None:
        """
        Handle incoming messages. Deserializes the event, parses the subject into a Topic,
        and calls the handler without blocking.
        """
        try:
            logger.debug(f"Received message: {msg.subject} with event data: {msg.data!r}")
            topic = Topic.from_subject(msg.subject)
            event_data = msg.data
            event = self.event_cls.deserialize_event(event_data)
            logger.debug(f"Deserialized event: {event}")
            asyncio.create_task(self._run_handler_with_error_handling(event, topic, msg.subject))
        except Exception as e:
            logger.error(f"Error in message handler for subject '{msg.subject}': {e}")
            traceback.print_exc()

    async def _run_handler_with_error_handling(self, event, topic, subject):
        """Helper method to run handler with proper error handling"""
        try:
            await self.handler(event, topic)
        except Exception as e:
            logger.error(f"Error in async handler for subject '{subject}': {e}")
            traceback.print_exc()


    @classmethod
    def all_for_agent_display_events(
        cls,
        nc: NATS,
        topic_manager: TopicManager,
        handler: Callable[[DisplayEvent, Topic], Awaitable[None]],
    ):
        """Subscribe to all display events from all agents."""
        subject = topic_manager.get_subject_for_all_display_events_in_agent()
        return cls(
            nc=nc,
            subject=subject,
            event_cls=DisplayEvent,
            handler=handler,
        )

    @classmethod
    def for_thread_display_events(
        cls,
        nc: NATS,
        topic_manager: AgentThreadTopicManager,
        handler: Callable[[DisplayEvent, Topic], Awaitable[None]],
    ):
        """Subscribe to all display events within a specific thread."""
        subject = topic_manager.get_subject_for_display_event_in_thread("*", "*")
        return cls(
            nc=nc,
            subject=subject,
            event_cls=DisplayEvent,
            handler=handler,
        )


    @classmethod
    def for_all_thread_events(
        cls,
        nc: NATS,
        topic_manager: AgentThreadTopicManager,
        handler: Callable[[ControlEvent, Topic], Awaitable[None]],
    ):
        """Subscribe to all events (display, control, etc.) within a specific thread."""
        subject = topic_manager.get_subject_for_all_event_in_thread("*", "*")
        return cls(
            nc=nc,
            subject=subject,
            event_cls=BaseEvent,
            handler=handler,
        )

    @classmethod
    def for_agent_discovery_request_events(
        cls,
        nc: NATS,
        topic_manager: TopicManager,
        handler: Callable[[BaseEvent, Topic], Awaitable[None]],
        call_id: str = "*",
    ):
        """Subscribe to discovery request events for agents, optionally filtered by a specific call_id."""
        subject = topic_manager.get_agent_discovery_subject_request(call_id)
        return cls(
            nc=nc,
            subject=subject,
            event_cls=BaseEvent,
            handler=handler,
        )

    @classmethod
    def for_agent_discovery_response_events(
        cls,
        nc: NATS,
        topic_manager: TopicManager,
        handler: Callable[[BaseEvent, Topic], Awaitable[None]],
        call_id: str = "*",
    ):
        """Subscribe to discovery response events for agents, optionally filtered by a specific call_id."""
        subject = topic_manager.get_agent_discovery_subject_response(call_id)
        return cls(
            nc=nc,
            subject=subject,
            event_cls=BaseEvent,
            handler=handler,
        )
