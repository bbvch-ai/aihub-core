import logging
from typing import Annotated, Any, Dict, List, Optional

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

    async def get_json_value(self, run_id: str, key: str, default_value: Any = None) -> Any:
        """
        Get a JSON value from Redis with caching.
        Uses TTLCache to automatically expire entries after 5 minutes.
        """
        # Create a unique cache key combining run_id and key
        cache_key = f"{run_id}:{key}"

        # Check if the value is in cache
        if cache_key in self._cache:
            logger.debug(f"Cache hit for {cache_key}")
            return self._cache[cache_key]

        # If not in cache, get the value from Redis
        result = await super().get_json_value(run_id, key, default_value)

        # Cache the result (TTLCache will automatically expire it after the TTL)
        self._cache[cache_key] = result
        logger.debug(f"Cached value for {cache_key}")

        return result

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

        # Create a unique key for this event
        key = f"{event_type}.{event_id}"

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
            event_data = await self.get_json_value(run_id, key)
            if event_data:
                events.append(ControlEvent.deserialize_event(event_data))

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
        event_map: Dict[str, List[ControlEvent]] = {class_name: [] for class_name in class_names}

        # Create a pattern that matches any of the specified class names
        # Using Redis key pattern: {class_name1}.*|{class_name2}.*|...
        combined_pattern = "|".join(f"{class_name}.*" for class_name in class_names)
        all_matching_keys = await self.get_all_keys(run_id, combined_pattern)

        # Retrieve all matching events in a single batch
        for key in all_matching_keys:
            event_data = await self.get_json_value(run_id, key)
            if event_data:
                event = ControlEvent.deserialize_event(event_data)
                # Determine which class this event belongs to
                for class_name in class_names:
                    if key.startswith(f"{class_name}."):
                        if before is None or event.created_at <= before:
                            event_map[class_name].append(event)
                        break

        logger.debug(f"Retrieved events for types: {', '.join(class_names)}")
        return event_map
