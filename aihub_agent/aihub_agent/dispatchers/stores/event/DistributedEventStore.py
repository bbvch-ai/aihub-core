import json
from typing import Annotated, Dict, List, Optional, Type

from aihub_lib.nats.events import ControlEvent
from nats.js import JetStreamContext

from aihub_agent.dispatchers.stores.StoreBase import StoreBase


class DistributedEventStore(StoreBase):
    """
    A run-scoped store for persisting and retrieving Events (subclasses of ControlEvent) associated with a single run.

    ### Why DistributedEventStore?
    When executing workflows, steps may depend on historical Events. The DistributedEventStore ensures that
    all Events for a given run are persisted in a JetStream KV store, making them accessible across
    distributed environments and restarts.

    ### Key Operations
    - **store_event(run_id, event):**
      Appends the new event to the list of Events for its type, ensuring no duplicate `event_id` entries.
      Stores Events in a type-wise manner (e.g., all StartEvents together, all StopEvents together).

    - **get_events_of_type(run_id, event_type):**
      Fetches all Events of a specific type for the given run, deserializing them into event objects.

    - **get_all_events(run_id, before=None):**
      Retrieves all Events for a run, optionally filtered by a timestamp (only Events created_at ≤ before).
      Useful for determining whether enough Events have occurred to trigger certain steps.

    ### Persistence Details
    - Each run has its own bucket (e.g. "events_RUNID").
    - Keys in the bucket correspond to event type names (e.g. "StartEvent").
    - Values are JSON arrays of serialized event data, enabling quick retrieval by type.

    ### Example
    If a run has multiple StartEvent and StopEvent instances, `store_event` appends them to their respective arrays.
    Later, `get_events_of_type(run_id, StartEvent)` returns all recorded start Events for that run.

    """

    def __init__(self, js: JetStreamContext):
        super().__init__(js, prefix="Events")

    async def store_event(
        self,
        run_id: Annotated[str, "The identifier for the run."],
        event: Annotated[ControlEvent, "The event instance to store."],
    ):
        """
        Appends a new event to the run's event list for its type, ensuring no duplicates by `event_id`.
        """
        kv = await self._get_kv_store(run_id)
        event_type = event.__class__.__name__

        # Load existing Events for this type
        try:
            entry = await kv.get(event_type)
            event_list_data = json.loads(entry.value.decode())
        except Exception:
            event_list_data = []

        # Add the new event and remove duplicates
        event_list_data.append(event.model_dump())
        event_list_data = list({e["event_id"]: e for e in event_list_data}.values())

        # Save updated list
        await kv.put(event_type, json.dumps(event_list_data).encode())

    async def get_events_of_type(
        self,
        run_id: Annotated[str, "The run identifier."],
        event_type: Annotated[Type[ControlEvent], "The event subclass to fetch."],
    ) -> List[ControlEvent]:
        """
        Returns all Events of the specified type for the given run, reconstructed as event objects.
        If no Events exist for that type, returns an empty list.
        """
        kv = await self._get_kv_store(run_id)
        try:
            entry = await kv.get(event_type.__name__)
            event_list_data = json.loads(entry.value.decode())
            return [event_type(**data) for data in event_list_data]
        except Exception:
            return []

    async def get_all_events(
        self,
        run_id: Annotated[str, "The run identifier."],
        before: Annotated[Optional[int], "Filter timestamp; only include Events created_at ≤ before."] = None,
    ) -> Dict[str, List[ControlEvent]]:
        """
        Retrieves all Events for a run, organized by event type name.
        If `before` is provided, filters out Events created after that timestamp.

        Returns a dict keyed by event type name, with values being lists of event instances.
        """
        kv = await self._get_kv_store(run_id)
        events: Dict[str, List[ControlEvent]] = {}
        keys = await kv.keys()
        for key in keys:
            # Use the event registry to find the event class by name
            event_class = ControlEvent._event_registry.get(key)
            if event_class:
                event_list = await self.get_events_of_type(run_id, event_class)
                if before is not None:
                    event_list = [evt for evt in event_list if evt.created_at <= before]
                events[key] = event_list
        return events
