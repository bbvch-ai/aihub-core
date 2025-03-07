import logging
from typing import Dict, List, Optional

from aihub_lib.nats.events import ControlEvent
from cachetools import TTLCache
from redis.asyncio import Redis

from aihub_agent.dispatchers.stores.StoreBase import StoreBase

logger = logging.getLogger(__name__)


class DistributedEventStore(StoreBase):
    """
    A run-scoped store for persisting and retrieving events using Redis Lists with optimized storage.

    This implementation stores only event IDs in the type-specific lists, while the full event data
    is stored in individual keys. This significantly reduces the data transfer when retrieving lists
    of events, especially when many events already exist in the cache.
    """

    # Cache for deserialized events, keyed by run_id:event_type:event_id
    _event_cache = TTLCache(maxsize=10_000, ttl=300)

    def __init__(self, redis: Redis):
        super().__init__(redis, prefix="events")

    async def store_event(self, run_id: str, event: ControlEvent):
        """
        Stores an event by:
        1. Storing the full event data in an individual key
        2. Appending only the event ID to the type-specific list
        """
        event_type = event.__class__.__name__
        event_data = event.model_dump()
        event_id = event_data["event_id"]

        # Store the full event data
        event_key = f"data:{event_type}:{event_id}"
        await self.put_json_value(run_id, event_key, event_data)

        # Add only the event ID to the list of events of this type
        list_key = f"list:{event_type}"
        success = await self.append_to_list(run_id, list_key, event_id.encode())

        # Cache the event
        cache_key = f"{run_id}:{event_type}:{event_id}"
        self._event_cache[cache_key] = event

        if success:
            logger.debug(f"Stored event {event_type} with ID {event_id}")
        else:
            logger.error(f"Failed to store event {event_type} with ID {event_id}")

    async def get_event_by_id(self, run_id: str, event_type: str, event_id: str) -> Optional[ControlEvent]:
        """Gets an event by its type and ID, using cache if available."""
        cache_key = f"{run_id}:{event_type}:{event_id}"

        # Check cache first
        if cache_key in self._event_cache:
            logger.debug(f"Cache hit for event {event_type}:{event_id}")
            return self._event_cache[cache_key]

        # Cache miss, get from Redis
        logger.debug(f"Cache miss for event {event_type}:{event_id}")
        event_key = f"data:{event_type}:{event_id}"
        event_data = await self.get_json_value(run_id, event_key)

        if not event_data:
            logger.warning(f"Event {event_type}:{event_id} not found in Redis")
            return None

        # Deserialize and cache
        event = ControlEvent.deserialize_event(event_data)
        self._event_cache[cache_key] = event
        return event

    async def get_events_of_type(
        self, run_id: str, class_name: str, before: Optional[int] = None
    ) -> List[ControlEvent]:
        """
        Returns all events of the specified type, using an optimized approach:
        1. Retrieve the list of event IDs (much smaller data transfer)
        2. Fetch full events from cache when available
        3. Only retrieve missing events from Redis
        """
        list_key = f"list:{class_name}"

        # Get the list of event IDs (much faster than retrieving full events)
        event_ids = await self.get_list(run_id, list_key, lambda v: v.decode())

        events = []
        # First batch: try to get events from cache or Redis
        for event_id in event_ids:
            event = await self.get_event_by_id(run_id, class_name, event_id)
            if event is None:
                continue

            # Apply time filter if specified
            if before is not None and event.created_at > before:
                continue

            events.append(event)

        return events

    async def get_events_of_multiple_types(
        self, run_id: str, class_names: List[str], before: Optional[int] = None
    ) -> Dict[str, List[ControlEvent]]:
        """Retrieves events for multiple types, organized by event type name."""
        event_map: Dict[str, List[ControlEvent]] = {}

        for class_name in class_names:
            events = await self.get_events_of_type(run_id, class_name, before)
            event_map[class_name] = events

        return event_map
