import asyncio
import logging
import uuid
from typing import Annotated

from cachetools import TTLCache
from nats.aio.client import Client as NATS
from nats.js import JetStreamContext
from nats.js.api import AckPolicy, DeliverPolicy

from aihub_lib.nats.dispatcher.stores.event.ExecutionContextEventStore import ExecutionContextEventStore
from aihub_lib.nats.events import BaseEvent
from aihub_lib.nats.polling.JSPoller import JSPoller
from aihub_lib.nats.streams.StreamManager import StreamManager
from aihub_lib.nats.topic_managers.AbstractStreamTopicManager import AbstractStreamTopicManager
from aihub_lib.nats.topics import Topic

logger = logging.getLogger(__name__)


class JetStreamEventStore:
    """
    A distributed event store powered by NATS JetStream for reliable, consistent event management.

    ### Why JetStreamEventStore?
    In distributed workflows, events drive the progress of executions. These events need to be:
    - Durably stored for reliability
    - Quickly accessible for efficiency
    - Consistently available across server restarts or outages
    - Replayed in order when a service comes online

    JetStreamEventStore solves these challenges by:
    - Using NATS JetStream's persistent storage for durability
    - Maintaining an in-memory cache for fast lookups
    - Automatically replaying ALL historical messages when starting up
    - Ensuring consistent event ordering based on timestamps
    - Providing synchronization primitives for waiting on events

    ### Key Features
    1. **Full History Replay**: Automatically replays all historical events when starting up.
    2. **In-Memory Caching**: Stores events in memory for fast access while maintaining JetStream
       as the authoritative source.
    3. **Event Synchronization**: Provides mechanisms to wait for specific events to arrive.
    4. **ExecutionContext-Scoped Storage**: Organizes events execution context for clean separation between workflows.
    5. **Automatic Cleanup**: Uses TTLCache to automatically expire old execution contexts after configurable periods.

    ### Lifecycle
    - **Initialization**: On startup, subscribes to JetStream and replays all historical events.
    - **Operation**: Maintains events in memory, categorized by execution context and event type.
    - **Cleanup**: Automatically expires old execution contexts from memory after the configured TTL.

    ### Integration Points
    This store is designed to be a direct replacement for the Redis-based DistributedEventStore,
    providing the same API but leveraging NATS JetStream for better durability and performance.
    It integrates seamlessly with the `Dispatcher` to drive workflow execution.
    """

    def __init__(
        self,
        nc: Annotated[NATS, "NATS client for messaging"],
        js: Annotated[JetStreamContext, "JetStream context for persistent storage"],
        topic_manager: Annotated[AbstractStreamTopicManager, "Topic manager with stream capabilities"],
        topic: Annotated[type[Topic], "Topic under which these events were published"],
        # 30 days default TTL
        ttl_seconds: Annotated[int, "Time-to-live for cached execution context data in seconds"] = 60 * 60 * 24 * 30,
    ):
        self.nc = nc
        self.js = js
        self.topic_manager = topic_manager
        self.topic = topic

        # TTLCache for storing execution context events - entire execution contexts expire together after ttl_seconds
        self.execution_context_stores = TTLCache(maxsize=100_000, ttl=ttl_seconds)

        # Synchronization for events being processed
        self.pending_events: set[str] = set()
        self.event_sync_conditions: dict[str, asyncio.Condition] = {}
        self._background_tasks: set[asyncio.Task] = set()

        # Subscription
        self.subscription = None

        logger.debug(f"New JetStream Event Store created for topic {self.topic_manager}")
        # Initialization flag
        self.is_initialized = False
        self.init_lock = asyncio.Lock()

        self.stream_name, self.stream_subject = self.topic_manager.get_stream()
        self.control_subject = self.topic_manager.get_subject_for_all_control_events()

        uuid_hex = uuid.uuid4().hex
        self.subscription_durable_name = f"event-store-{uuid_hex}"
        self.replay_durable_name = f"event-store-replay-{uuid_hex}"

    async def start(self):
        """
        Initialize the event store by:
        1. Ensuring the required stream exists
        2. Replaying historical events from JetStream
        3. Setting up a subscription for new events
        """
        async with self.init_lock:
            if self.is_initialized:
                return

            logger.debug(f"Starting JetStream Event Store with stream name {self.stream_name}")
            logger.debug(f"Starting JetStream Event Store with stream subject {self.stream_subject}")
            logger.debug(f"Starting JetStream Event Store with control subject {self.control_subject}")

            # Step 1: Ensure the stream exists
            stream_manager = StreamManager(self.js, self.stream_name, self.stream_subject)
            await stream_manager.ensure_stream_exists()
            logger.debug(f"Ensured stream {self.stream_name} exists")

            # Step 2: Subscribe to new events
            self.subscription = await self.js.subscribe(
                subject=self.control_subject,
                durable=self.subscription_durable_name,
                stream=self.stream_name,
                cb=self._handle_new_event,
            )

            logger.debug(f"Subscribed to {self.control_subject} for new events")

            # Step 3: Replay historical events
            try:
                poller = JSPoller(
                    js=self.js,
                    stream_name=self.stream_name,
                    stream_subject=self.control_subject,
                    consumer_name=self.replay_durable_name,
                )

                await poller.ensure_consumer_exists(
                    deliver_policy=DeliverPolicy.ALL,
                    ack_policy=AckPolicy.NONE,
                    filter_subject=self.control_subject,
                )

                msg_count = 0
                while True:
                    batch_had_messages = False
                    async for polled_msg in poller.poll(batch_size=100, timeout=1.0):
                        batch_had_messages = True
                        try:
                            topic = self.topic.from_subject(polled_msg.subject)
                            event = polled_msg.event
                            event._jetstream_sequence = polled_msg.sequence
                            self._add_event_to_store(topic.execution_context_id, event)
                            msg_count += 1
                        except Exception as e:
                            logger.exception(f"Error processing replayed message: {e}")

                    if not batch_had_messages:
                        break

                logger.info(f"Replayed {msg_count} historical events")

                try:
                    await self.js.delete_consumer(self.stream_name, self.replay_durable_name)
                except Exception as e:
                    logger.warning(f"Error deleting temporary consumer: {e}")

                self.is_initialized = True
                logger.info("Event store initialization complete")

            except Exception as e:
                logger.exception(f"Error initializing event store: {e}")
                raise

    async def stop(self):
        """
        Stop the event store by unsubscribing from JetStream.
        """
        if self.subscription:
            await self.subscription.unsubscribe()
            self.subscription = None

        self.is_initialized = False
        logger.info("Event store stopped")

    def _get_execution_context_store(self, store_execution_context_id: str) -> ExecutionContextEventStore:
        """Get or create a ExecutionContextEventStore for the specified store_execution_context_id"""
        if store_execution_context_id not in self.execution_context_stores:
            self.execution_context_stores[store_execution_context_id] = ExecutionContextEventStore()
        return self.execution_context_stores[store_execution_context_id]

    def _add_event_to_store(self, store_execution_context_id: str, event: BaseEvent):
        """Add an event to the store and handle any pending synchronization"""
        execution_context_store = self._get_execution_context_store(store_execution_context_id)
        execution_context_store.add_event(event)

        # Signal if this event was being waited for
        event_name = event.event_name
        event_id = event.event_id
        event_key = f"{store_execution_context_id}:{event_name}:{event_id}"

        if event_key in self.pending_events:
            self.pending_events.remove(event_key)

            if event_key in self.event_sync_conditions:
                condition = self.event_sync_conditions[event_key]
                task = asyncio.create_task(self._notify_condition(condition))
                self._background_tasks.add(task)
                task.add_done_callback(self._background_tasks.discard)

    async def _notify_condition(self, condition):
        """Helper to notify a condition and clean it up."""
        async with condition:
            condition.notify_all()

    async def _handle_new_event(self, msg):
        """
        Callback for handling new events from the JetStream subscription.
        """
        try:
            logger.debug(f"Received message: {msg.subject}")
            topic = self.topic.from_subject(msg.subject)
            store_execution_context_id = topic.execution_context_id
            event = BaseEvent.deserialize_event(msg.data)
            event._jetstream_sequence = msg.metadata.sequence.stream
            logger.debug(f"Deserialized event: {event.event_name}")

            self._add_event_to_store(store_execution_context_id, event)

            # Acknowledge the message
            await msg.ack()
        except Exception as e:
            logger.exception(e)
            logger.exception(f"Error in message handler for subject '{msg.subject}': {e}")
            # Still ack the message to avoid redelivery
            try:
                await msg.ack()
            except Exception:
                pass

    async def ensure_event_stored(
        self,
        store_execution_context_id: Annotated[str, "Unique identifier for the jetstream store context"],
        event: Annotated[BaseEvent, "The event to ensure is stored"],
        timeout: Annotated[float, "Maximum time to wait in seconds"] = 10.0,
    ) -> bool:
        """
        Ensures that the event is stored in the event store.
        If not already stored, waits until it is stored or the timeout expires.

        Returns True if the event is stored, False if the timeout expired.
        """
        event_name = event.event_name
        event_id = event.event_id

        execution_context_store = self._get_execution_context_store(store_execution_context_id)
        if event_id in execution_context_store.events.get(event_name, {}):
            return True

        # If not stored, create a condition to wait for it
        event_key = f"{store_execution_context_id}:{event_name}:{event_id}"
        self.pending_events.add(event_key)

        if event_key not in self.event_sync_conditions:
            self.event_sync_conditions[event_key] = asyncio.Condition()

        condition = self.event_sync_conditions[event_key]

        # Wait for the event to be stored or timeout
        try:
            async with condition:
                if event_id in execution_context_store.events.get(event_name, {}):
                    return True

                # Wait for the condition to be notified
                try:
                    await asyncio.wait_for(condition.wait(), timeout=timeout)
                    return True
                except TimeoutError:
                    logger.warning(f"Timeout waiting for event {event_key} to be stored")
                    return False
        finally:
            # Clean up
            if event_key in self.pending_events:
                self.pending_events.remove(event_key)

            async with condition:
                if not condition._waiters:  # pylint: disable=protected-access
                    del self.event_sync_conditions[event_key]

    async def get_events_of_type(
        self,
        store_execution_context_id: Annotated[str, "Unique identifier for the jetstream store context"],
        class_name: Annotated[str, "The event class name to retrieve"],
        until_event: Annotated[BaseEvent | None, "Only include events created until this event was received"] = None,
    ) -> list[BaseEvent]:
        """
        Retrieves all events of the specified type for a execution context.
        If 'until' is specified, only returns events created until that timestamp.
        """
        execution_context_store = self._get_execution_context_store(store_execution_context_id)
        return execution_context_store.get_events_of_name(class_name, until_event)

    async def get_events_of_multiple_types(
        self,
        store_execution_context_id: Annotated[str, "Unique identifier for the jetstream store context"],
        class_names: Annotated[list[str], "List of event class names to retrieve"],
        until_event: Annotated[BaseEvent | None, "Only include events created until this event was received"] = None,
    ) -> dict[str, list[BaseEvent]]:
        """
        Retrieves events for multiple types, organized by event type name.
        This is the primary method used by the Dispatcher.
        """
        execution_context_store = self._get_execution_context_store(store_execution_context_id)
        return execution_context_store.get_events_of_multiple_names(class_names, until_event)

    async def delete_all(
        self, store_execution_context_id: Annotated[str, "Unique identifier for the jetstream store context"]
    ):
        """
        Removes all events for a specific execution context.
        """
        if store_execution_context_id in self.execution_context_stores:
            del self.execution_context_stores[store_execution_context_id]

        logger.debug(f"Deleted all events for execution context {store_execution_context_id}")
