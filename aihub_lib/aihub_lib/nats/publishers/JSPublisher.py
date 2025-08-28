import asyncio
import logging
import uuid

from nats.js import JetStreamContext

from aihub_lib.nats.publishers.AbstractPublisher import AbstractPublisher, TEvent

logger = logging.getLogger(__name__)


class JSPublisher(AbstractPublisher[TEvent]):
    """
    A publisher that integrates with NATS JetStream, ensuring events are stored in streams
    for durability, replay, and at-least-once delivery semantics.

    ### Why JSPublisher?
    While NCPublisher publishes events to ephemeral subjects, JSPublisher leverages JetStream.
    By publishing events via `js.publish`, messages are persisted according to stream configurations.
    This is essential for systems that need guaranteed message retention, auditing, or replaying.

    ### Features
    - **Durable Storage:** Events are written to JetStream-managed streams.
    - **Type-Awareness & Logging:** Similar to NCPublisher, it logs events, checks event-subject alignment,
      and warns if, for example, a control event is published to a display subject.
    """

    def __init__(self, js: JetStreamContext):
        self.js = js

    async def publish_event(self, event: TEvent, subject: str, retries=10):
        """
        Publishes the given event to the specified JetStream subject, encoding it as JSON.

        Logs event details and warns if event type does not match the subject pattern.
        This ensures developers can catch configuration issues early and maintain consistent
        event routing conventions.
        """
        self._detect_and_log_subject_mismatch(event, subject)

        logger.debug(f"Publishing event {event.event_name} to {subject}")
        serialized_event = event.model_dump_json(serialize_as_any=True)
        logger.debug(f"Serialized event: {event.event_name}({serialized_event})")

        message_id = str(uuid.uuid4())
        headers = {"Nats-Msg-Id": message_id}  # Deduplication

        for attempt in range(retries):
            try:
                future = await asyncio.wait_for(
                    self.js.publish_async(subject, serialized_event.encode(), headers=headers), timeout=5
                )
                ack = await asyncio.wait_for(future, timeout=5)
                logger.debug(f"Publish ACK received: {ack}")
                return  # Success, no retry needed
            except TimeoutError:
                logger.warning(f"Publish timeout ({attempt + 1}/{retries}) for {event.event_name} to subject {subject}")
            except Exception as e:
                logger.exception(f"NATS error while publishing event {event.event_name} to subject {subject}: {e}")

            await asyncio.sleep(1)  # Wait before retrying

        logger.exception(f"Failed to publish event {event.event_name} to subject {subject} after {retries} attempts")
