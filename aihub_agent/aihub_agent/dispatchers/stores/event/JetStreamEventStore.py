import asyncio
import logging
import uuid
from typing import Annotated, Dict, List, Optional, Set

from aihub_lib.nats.events import ControlEvent
from aihub_lib.nats.streams.StreamManager import StreamManager
from aihub_lib.nats.topic_managers.agents.AgentInstanceTopicManager import AgentInstanceTopicManager
from aihub_lib.nats.topics.agents.AgentTopic import AgentTopic
from cachetools import TTLCache
from nats.aio.client import Client as NATS
from nats.js import JetStreamContext
from nats.js.api import AckPolicy, ConsumerConfig, DeliverPolicy

from aihub_agent.dispatchers.stores.event.RunEventStore import RunEventStore

logger = logging.getLogger(__name__)


class JetStreamEventStore:
    """
    A distributed event store powered by NATS JetStream for reliable, consistent event management.

    ### Why JetStreamEventStore?
    In distributed workflows, events drive the progress of runs. These events need to be:
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
    1. **Full History Replay**: Automatically replays all historical events for this agent when starting up.
    2. **In-Memory Caching**: Stores events in memory for fast access while maintaining JetStream as the authoritative source.
    3. **Event Synchronization**: Provides mechanisms to wait for specific events to arrive.
    4. **Run-Scoped Storage**: Organizes events by run ID for clean separation between workflows.
    5. **Automatic Cleanup**: Uses TTLCache to automatically expire old runs after configurable periods.

    ### Lifecycle
    - **Initialization**: On startup, subscribes to JetStream and replays all historical events.
    - **Operation**: Maintains events in memory, categorized by run and event type.
    - **Cleanup**: Automatically expires old runs from memory after the configured TTL.

    ### Integration Points
    This store is designed to be a direct replacement for the Redis-based DistributedEventStore,
    providing the same API but leveraging NATS JetStream for better durability and performance.
    It integrates seamlessly with the `Dispatcher` to drive workflow execution.
    """

    def __init__(
        self,
        nc: Annotated[NATS, "NATS client for messaging"],
        js: Annotated[JetStreamContext, "JetStream context for persistent storage"],
        topic_manager: Annotated[AgentInstanceTopicManager, "Topic manager for this agent instance"],
        ttl_seconds: Annotated[int, "Time-to-live for cached run data in seconds"] = 60 * 60 * 24 * 30,
        # 30 days default TTL
    ):
        self.nc = nc
        self.js = js
        self.topic_manager = topic_manager

        # TTLCache for storing run events - entire runs expire together after ttl_seconds
        self.run_stores = TTLCache(maxsize=100_000, ttl=ttl_seconds)

        # Synchronization for events being processed
        self.pending_events: Set[str] = set()
        self.event_sync_conditions: Dict[str, asyncio.Condition] = {}

        # Subscription
        self.subscription = None

        logger.debug(
            f"New JetStream Event Store created for agent {self.topic_manager.agent_class}.{self.topic_manager.agent_id}"
        )
        # Initialization flag
        self.is_initialized = False
        self.init_lock = asyncio.Lock()

        self.stream_name, self.stream_subject = self.topic_manager.get_stream_over_agent()
        self.control_subject = self.topic_manager.get_subject_for_all_control_events_in_agent()

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
            await stream_manager.ensure_agent_stream_exists()
            logger.debug(f"Ensured stream {self.stream_name} exists")

            # Step 2: Subscribe to new events
            # Generate a unique durable name for this instance
            durable_name = f"event-store-{uuid.uuid4().hex}"

            self.subscription = await self.js.subscribe(
                subject=self.control_subject,
                durable=durable_name,
                stream=self.stream_name,
                cb=self._handle_new_event,
            )

            logger.debug(f"Subscribed to {self.control_subject} for new events")

            # Step 3: Replay historical events
            try:
                # Create a pull subscription for historical replay
                replay_config = ConsumerConfig(
                    name=f"event-store-replay-{id(self):x}",
                    filter_subject=self.control_subject,
                    ack_policy=AckPolicy.NONE,
                    deliver_policy=DeliverPolicy.ALL,
                )

                # Create the consumer for replay
                await self.js.add_consumer(self.stream_name, config=replay_config)

                # Create a pull subscription
                pull_sub = await self.js.pull_subscribe(
                    subject=self.control_subject,
                    durable=f"event-store-replay-{id(self):x}",
                    stream=self.stream_name,
                )

                # Fetch and process all historical events
                msg_count = 0
                while True:
                    try:
                        # Fetch a batch of messages
                        messages = await pull_sub.fetch(batch=100, timeout=1)
                        if not messages:
                            break  # No more messages

                        for msg in messages:
                            try:
                                topic = AgentTopic.from_subject(msg.subject)
                                event = ControlEvent.deserialize_event(msg.data)
                                self._add_event_to_store(topic.run_id, event)
                                msg_count += 1
                            except Exception as e:
                                logger.error(f"Error processing replayed message: {e}")
                    except Exception as e:
                        if "timeout" in str(e).lower():
                            break  # No more messages
                        logger.error(f"Error fetching messages: {e}")
                        break

                logger.info(f"Replayed {msg_count} historical events")

                # Clean up the temporary consumer
                try:
                    await self.js.delete_consumer(self.stream_name, f"event-store-replay-{id(self):x}")
                except Exception as e:
                    logger.warning(f"Error deleting temporary consumer: {e}")

                self.is_initialized = True
                logger.info("Event store initialization complete")

            except Exception as e:
                logger.error(f"Error initializing event store: {e}")
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

    def _get_run_store(self, run_id: str) -> RunEventStore:
        """Get or create a RunEventStore for the specified run_id"""
        if run_id not in self.run_stores:
            self.run_stores[run_id] = RunEventStore()
        return self.run_stores[run_id]

    def _add_event_to_store(self, run_id: str, event: ControlEvent):
        """Add an event to the store and handle any pending synchronization"""
        # Get the run store and add the event
        run_store = self._get_run_store(run_id)
        run_store.add_event(event)

        # Signal if this event was being waited for
        event_type = event.__class__.__name__
        event_id = event.event_id
        event_key = f"{run_id}:{event_type}:{event_id}"

        if event_key in self.pending_events:
            self.pending_events.remove(event_key)

            if event_key in self.event_sync_conditions:
                condition = self.event_sync_conditions[event_key]
                asyncio.create_task(self._notify_condition(condition))

    async def _notify_condition(self, condition):
        """Helper to notify a condition and clean it up."""
        async with condition:
            condition.notify_all()

    async def _handle_new_event(self, msg):
        """
        Callback for handling new events from the JetStream subscription.
        """
        try:
            topic = AgentTopic.from_subject(msg.subject)
            run_id = topic.run_id
            event = ControlEvent.deserialize_event(msg.data)

            # Add the event to the store
            self._add_event_to_store(run_id, event)

            # Acknowledge the message
            await msg.ack()
        except Exception as e:
            logger.error(f"Error handling new event: {e}")
            # Still ack the message to avoid redelivery
            try:
                await msg.ack()
            except Exception:
                pass

    async def ensure_event_stored(
        self,
        run_id: Annotated[str, "Unique identifier for the workflow run"],
        event: Annotated[ControlEvent, "The event to ensure is stored"],
        timeout: Annotated[float, "Maximum time to wait in seconds"] = 10.0,
    ) -> bool:
        """
        Ensures that the event is stored in the event store.
        If not already stored, waits until it is stored or the timeout expires.

        Returns True if the event is stored, False if the timeout expired.
        """
        event_type = event.__class__.__name__
        event_id = event.event_id

        # Check if the event is already stored
        run_store = self._get_run_store(run_id)
        if event_id in run_store.events.get(event_type, {}):
            return True

        # If not stored, create a condition to wait for it
        event_key = f"{run_id}:{event_type}:{event_id}"
        self.pending_events.add(event_key)

        if event_key not in self.event_sync_conditions:
            self.event_sync_conditions[event_key] = asyncio.Condition()

        condition = self.event_sync_conditions[event_key]

        # Wait for the event to be stored or timeout
        try:
            async with condition:
                # Check again in case it arrived while we were setting up
                if event_id in run_store.events.get(event_type, {}):
                    return True

                # Wait for the condition to be notified
                try:
                    await asyncio.wait_for(condition.wait(), timeout=timeout)
                    return True
                except asyncio.TimeoutError:
                    logger.warning(f"Timeout waiting for event {event_key} to be stored")
                    return False
        finally:
            # Clean up
            if event_key in self.pending_events:
                self.pending_events.remove(event_key)

            # Remove the condition if there are no more waiters
            async with condition:
                if not condition._waiters:  # pylint: disable=protected-access
                    del self.event_sync_conditions[event_key]

    async def get_events_of_type(
        self,
        run_id: Annotated[str, "Unique identifier for the workflow run"],
        class_name: Annotated[str, "The event class name to retrieve"],
        before: Annotated[Optional[int], "Only include events created before this timestamp"] = None,
    ) -> List[ControlEvent]:
        """
        Retrieves all events of the specified type for a run.
        If 'before' is specified, only returns events created before that timestamp.
        """
        run_store = self._get_run_store(run_id)
        return run_store.get_events_of_type(class_name, before)

    async def get_events_of_multiple_types(
        self,
        run_id: Annotated[str, "Unique identifier for the workflow run"],
        class_names: Annotated[List[str], "List of event class names to retrieve"],
        before: Annotated[Optional[int], "Only include events created before this timestamp"] = None,
    ) -> Dict[str, List[ControlEvent]]:
        """
        Retrieves events for multiple types, organized by event type name.
        This is the primary method used by the Dispatcher.
        """
        run_store = self._get_run_store(run_id)
        return run_store.get_events_of_multiple_types(class_names, before)

    async def delete_all(self, run_id: Annotated[str, "Unique identifier for the workflow run"]):
        """
        Removes all events for a specific run.
        """
        if run_id in self.run_stores:
            del self.run_stores[run_id]

        logger.debug(f"Deleted all events for run {run_id}")
