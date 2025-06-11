import asyncio
import logging
from typing import Awaitable, Callable, Optional, Type, TypeVar

from nats.aio.client import Client as NATS
from nats.aio.msg import Msg
from nats.aio.subscription import Subscription
from nats.errors import BadSubscriptionError, ConnectionDrainingError

from aihub_lib.nats.events import BaseEvent
from aihub_lib.nats.subscribers.AbstractSubscriber import AbstractSubscriber
from aihub_lib.nats.topics import Topic

logger = logging.getLogger(__name__)

TEvent = TypeVar("TEvent", bound=BaseEvent)


class NCSubscriber(AbstractSubscriber):
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
        super().__init__(nc, subject, event_cls, handler)
        self.subscription: Optional[Subscription] = None

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
            logger.exception(e)
            logger.exception(f"Error in message handler for subject '{msg.subject}': {e}")

    async def _run_handler_with_error_handling(self, event, topic, subject):
        """Helper method to run handler with proper error handling"""
        try:
            await self.handler(event, topic)
        except Exception as e:
            logger.exception(e)
            logger.exception(f"Error in async handler for subject '{subject}': {e}")
