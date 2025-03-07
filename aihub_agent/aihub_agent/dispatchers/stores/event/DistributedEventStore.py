import logging
from typing import Annotated, Dict, List, Optional

from aihub_lib.nats.events import ControlEvent
from cachetools import TTLCache
from redis.asyncio import Redis

from aihub_agent.dispatchers.stores.StoreBase import StoreBase

logger = logging.getLogger(__name__)


class DistributedEventStore(StoreBase):
    """
    A run-scoped store for persisting and retrieving events (subclasses of ControlEvent) associated with a single run.

    ### Why DistributedEventStore?
    When executing workflows, steps may depend on historical events. The DistributedEventStore ensures that
    all events for a given run are persisted in a JetStream KV store, making them accessible across
    distributed environments and restarts.

    ### Persistence Details
    - Each run has its own bucket (e.g. "events_RUNID").
    - Keys in the bucket correspond to event type names (e.g. "StartEvent").
    - Values are JSON arrays of serialized event data, enabling quick retrieval by type.

    ### Example
    If a run has multiple StartEvent and StopEvent instances, `store_event` appends them to their respective arrays.
    Later, `get_events_of_type(run_id, StartEvent)` returns all recorded start events for that run.
    """

    _cache = TTLCache(maxsize=10_000, ttl=300)

    def __init__(self, redis: Redis):
        super().__init__(redis, prefix="events")

    async def get_event(self, run_id: str, key: str) -> Optional[ControlEvent]:
        """
        Get a JSON value from Redis with caching.
        Uses TTLCache to automatically expire entries after 5 minutes.
        """
        # Create a unique cache key combining run_id and key
        cache_key = self._cache_key_from_key(run_id, key)

        # Check if the value is in cache
        if cache_key in self._cache:
            return self._cache[cache_key]

        logger.debug(f"Cache miss for {cache_key}")

        # If not in cache, get the value from Redis
        event_data = await self.get_json_value(run_id, key)

        if not event_data:
            return None

        event = ControlEvent.deserialize_event(event_data)

        # Cache the result (TTLCache will automatically expire it after the TTL)
        self._cache[cache_key] = event
        logger.debug(f"Cached value for {cache_key}")

        return event

    def _event_key(self, event_type: str, event_id: str) -> str:
        """Builds a namespaced Redis key for an event."""
        return f"{event_type}.{event_id}"

    def _cache_key(self, event_type: str, event_id: str, run_id: str) -> str:
        """Builds a unique cache key for a run and key."""
        key = self._event_key(event_type, event_id)
        return f"{run_id}:{key}"

    def _cache_key_from_key(self, run_id: str, key: str) -> str:
        """Builds a unique cache key for a run and key."""
        return f"{run_id}:{key}"

    async def store_event(
        self,
        run_id: Annotated[str, "The identifier for the run."],
        event: Annotated[ControlEvent, "The event instance to store."],
    ):
        """
        Stores an event in Redis using a direct key (ClassName.EventId).
        """
        event_type = event.__class__.__name__
        event_data = event.model_dump()
        event_id = event_data["event_id"]

        key = self._event_key(event_type, event_id)
        cache_key = self._cache_key(event_type, event_id, run_id)

        self._cache[cache_key] = event

        # Store the event directly
        success = await self.put_json_value(run_id, key, event_data)

        if success:
            logger.debug(f"Stored event {event_type} with ID {event_id} using key {key}")
        else:
            logger.error(f"Failed to store event {event_type} with ID {event_id}")

    async def get_events_of_type(
        self,
        run_id: Annotated[str, "The run identifier."],
        class_name: Annotated[str, "The event subclass name to fetch."],
    ) -> List[ControlEvent]:
        """
        Returns all events of the specified type by scanning for keys with the class name prefix.
        """
        events = []
        prefix = f"{class_name}.*"
        matching_keys = await self.get_all_keys(run_id, prefix)

        # Retrieve and deserialize each matching event
        for key in matching_keys:
            event = await self.get_event(run_id, key)
            if event is not None:
                events.append(event)

        logger.debug(f"Retrieved {len(events)} events of type {class_name}")
        return events

    async def get_events_of_multiple_types(
        self,
        run_id: Annotated[str, "The run identifier."],
        class_names: Annotated[List[str], "The event subclass names to fetch."],
        before: Annotated[Optional[int], "Filter timestamp; only include events created_at ≤ before."] = None,
    ) -> Dict[str, List[ControlEvent]]:
        """
        Retrieves all events for a run, organized by event type name.
        Uses a combined pattern to fetch keys for all event types in a single operation.
        """
        event_map: Dict[str, List[ControlEvent]] = {}

        for class_name in class_names:
            events = await self.get_events_of_type(run_id, class_name)
            event_map[class_name] = [event for event in events if before is None or event.created_at <= before]

        return event_map
