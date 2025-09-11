import asyncio
import logging
import uuid

from nats.js import JetStreamContext
from opentelemetry import trace

from aihub_lib.nats.publishers.AbstractPublisher import AbstractPublisher, TEvent
from aihub_lib.nats.tracing.NATSMessageHeaders import NATSMessageHeaders

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

    async def publish_event(self, event: TEvent, subject: str, retries=10, **kwargs):
        """
        Publishes the given event to the specified JetStream subject, encoding it as JSON.

        Logs event details and warns if event type does not match the subject pattern.
        This ensures developers can catch configuration issues early and maintain consistent
        event routing conventions.
        """
        tracer = trace.get_tracer(__name__)

        with tracer.start_as_current_span(f"JetStream.publish {subject}") as span:
            span.set_attribute("messaging.system", "nats.jetstream")
            span.set_attribute("messaging.destination", subject)
            span.set_attribute("messaging.operation", "publish")
            span.set_attribute("event.type", event.event_name)
            span.set_attribute("event.class", event.__class__.__name__)
            span.set_attribute("jetstream.retries", retries)

            try:
                self._detect_and_log_subject_mismatch(event, subject)

                logger.debug(f"Publishing event {event.event_name} to {subject}")
                serialized_event = event.model_dump_json(serialize_as_any=True)
                logger.debug(f"Serialized event: {event.event_name}({serialized_event})")

                message_id = str(uuid.uuid4())
                headers = NATSMessageHeaders().with_trace_context().with_header("Nats-Msg-Id", message_id).to_dict()

                for attempt in range(retries):
                    try:
                        span.set_attribute("jetstream.attempt", attempt + 1)

                        future = await asyncio.wait_for(
                            self.js.publish_async(subject, serialized_event.encode(), headers=headers), timeout=5
                        )
                        ack = await asyncio.wait_for(future, timeout=5)

                        span.set_attribute("jetstream.sequence", ack.seq)
                        span.set_attribute("jetstream.stream", ack.stream)
                        span.set_attribute("messaging.success", True)

                        logger.debug(f"Publish ACK received: {ack}")
                        return  # Success, no retry needed

                    except TimeoutError:
                        logger.warning(
                            f"Publish timeout ({attempt + 1}/{retries}) for {event.event_name} to subject {subject}"
                        )
                    except Exception as e:
                        logger.exception(
                            f"NATS error while publishing event {event.event_name} to subject {subject}: {e}"
                        )

                    await asyncio.sleep(1)  # Wait before retrying

                # If we get here, all retries failed
                error_msg = f"Failed to publish event {event.event_name} to subject {subject} after {retries} attempts"
                span.set_attribute("messaging.success", False)
                span.add_event("All publish attempts failed")
                logger.exception(error_msg)
                raise RuntimeError(error_msg)

            except Exception as e:
                span.set_attribute("messaging.success", False)
                span.record_exception(e)
                logger.exception(f"Failed to publish {event.event_name} to {subject}: {e}")
                raise
