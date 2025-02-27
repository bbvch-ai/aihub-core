import logging
from typing import Annotated, Dict, List, Optional

from aihub_lib.nats.events import ControlEvent
from nats.js import JetStreamContext

from aihub_agent.dispatchers.stores.StoreBase import StoreBase

logger = logging.getLogger(__name__)


class DistributedEventStore(StoreBase):
    """
    A run-scoped store for persisting and retrieving events (subclasses of ControlEvent) associated with a single run.

    ### Why DistributedEventStore?
    When executing workflows, steps may depend on historical events. The DistributedEventStore ensures that
    all events for a given run are persisted in a JetStream KV store, making them accessible across
    distributed environments and restarts.

    ### Key Operations
    - **store_event(run_id, event):**
      Appends the new event to the list of events for its type, ensuring no duplicate `event_id` entries.
      Stores events in a type-wise manner (e.g., all StartEvents together, all StopEvents together).

    - **get_events_of_type(run_id, event_type):**
      Fetches all events of a specific type for the given run, deserializing them into event objects.

    - **get_all_events(run_id, before=None):**
      Retrieves all events for a run, optionally filtered by a timestamp (only events created_at ≤ before).
      Useful for determining whether enough events have occurred to trigger certain steps.

    ### Persistence Details
    - Each run has its own bucket (e.g. "events_RUNID").
    - Keys in the bucket correspond to event type names (e.g. "StartEvent").
    - Values are JSON arrays of serialized event data, enabling quick retrieval by type.

    ### Example
    If a run has multiple StartEvent and StopEvent instances, `store_event` appends them to their respective arrays.
    Later, `get_events_of_type(run_id, StartEvent)` returns all recorded start events for that run.

    """

    def __init__(self, js: JetStreamContext):
        super().__init__(js, prefix="events")

    async def store_event(
        self,
        run_id: Annotated[str, "The identifier for the run."],
        event: Annotated[ControlEvent, "The event instance to store."],
    ):
        """
        Stores an event using a direct key (ClassName.EventId).
        This approach completely eliminates race conditions.
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
        kv = await self._get_kv_store(run_id)
        events = []

        try:
            # Get all keys in the store
            all_keys = await kv.keys()

            # Filter keys that match the class_name prefix
            prefix = f"{class_name}."
            matching_keys = [key for key in all_keys if key.startswith(prefix)]

            # Retrieve and deserialize each matching event
            for key in matching_keys:
                event_data = await self.get_json_value(run_id, key)
                if event_data:
                    events.append(ControlEvent.deserialize_event(event_data))

            logger.debug(f"Retrieved {len(events)} events of type {class_name}")
            return events

        except Exception as e:
            logger.error(f"Error fetching events of type {class_name}: {e}")
            return []

    async def get_all_events(
        self,
        run_id: Annotated[str, "The run identifier."],
        before: Annotated[Optional[int], "Filter timestamp; only include events created_at ≤ before."] = None,
    ) -> Dict[str, List[ControlEvent]]:
        """
        Retrieves all events for a run, organized by event type name.
        Scans all keys and groups them by class name.
        """
        kv = await self._get_kv_store(run_id)
        events: Dict[str, List[ControlEvent]] = {}

        try:
            # Get all keys
            all_keys = await kv.keys()

            # Process each key that contains a dot (indicating it's an event key)
            for key in all_keys:
                if "." not in key:
                    continue

                class_name, _ = key.split(".", 1)

                # Skip keys that aren't events (like utility keys)
                if class_name.startswith("_"):
                    continue

                # Fetch the event data
                event_data = await self.get_json_value(run_id, key)
                if not event_data:
                    continue

                # Deserialize the event
                event = ControlEvent.deserialize_event(event_data)

                # Apply timestamp filter if provided
                if before is not None and event.created_at > before:
                    continue

                # Add to the appropriate list in the result dictionary
                if class_name not in events:
                    events[class_name] = []
                events[class_name].append(event)

            # Log counts for debugging
            for class_name, event_list in events.items():
                logger.debug(f"Retrieved {len(event_list)} total events of type {class_name}")

        except Exception as e:
            logger.error(f"Error retrieving all events: {e}")

        return events
