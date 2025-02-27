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
        Appends a new event to the run's event list for its type.
        Uses synchronized_update to safely handle concurrent updates.
        """
        event_type = event.__class__.__name__
        event_data = event.model_dump()
        event_id = event_data["event_id"]

        # Define update function for synchronized operation
        def update_event_list(current_list):
            # Start with empty list if none exists
            if current_list is None:
                current_list = []

            # Check if this event ID already exists
            existing_ids = {e["event_id"] for e in current_list}

            # Only add if not a duplicate
            if event_id not in existing_ids:
                current_list.append(event_data)
                logger.debug(f"Adding event {event_type} with ID {event_id}. " f"Total count: {len(current_list)}")
            else:
                logger.debug(f"Event {event_type} with ID {event_id} already exists, skipping")

            return current_list

        # Perform the synchronized update
        success = await self.synchronized_update(run_id, event_type, update_event_list, default_value=[])

        if not success:
            logger.error(f"Failed to store event of type {event_type}")

    async def get_events_of_type(
        self,
        run_id: Annotated[str, "The run identifier."],
        class_name: Annotated[str, "The event subclass name to fetch."],
    ) -> List[ControlEvent]:
        """Returns all events of the specified type for the given run."""
        # Get the raw JSON data
        event_list_data = await self.get_json_value(run_id, class_name, default_value=[])

        # Convert to event objects
        events = [ControlEvent.deserialize_event(data) for data in event_list_data]
        logger.debug(f"Retrieved {len(events)} events of type {class_name}")
        return events

    async def get_all_events(
        self,
        run_id: Annotated[str, "The run identifier."],
        before: Annotated[Optional[int], "Filter timestamp; only include events created_at ≤ before."] = None,
    ) -> Dict[str, List[ControlEvent]]:
        """Retrieves all events for a run, organized by event type name."""
        kv = await self._get_kv_store(run_id)
        events: Dict[str, List[ControlEvent]] = {}

        try:
            class_names = await kv.keys()
            # Filter out mutex keys
            class_names = [name for name in class_names if not name.startswith("mutex_")]

            for class_name in class_names:
                # Get events for this type
                event_list = await self.get_events_of_type(run_id, class_name)

                # Apply timestamp filter if provided
                if before is not None:
                    event_list = [evt for evt in event_list if evt.created_at <= before]
                    logger.debug(f"After timestamp filtering, {len(event_list)} events of type {class_name} remain")

                events[class_name] = event_list

            # Log counts for debugging
            for class_name, event_list in events.items():
                logger.debug(f"Retrieved {len(event_list)} total events of type {class_name}")

        except Exception as e:
            logger.error(f"Error retrieving all events: {e}")

        return events
