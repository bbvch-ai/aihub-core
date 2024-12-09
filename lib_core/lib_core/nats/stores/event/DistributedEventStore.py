import json
from typing import Dict, List, Type, Optional

from nats.js import JetStreamContext

from lib_core.nats.events import ControlEvent
from lib_core.nats.stores.StoreBase import StoreBase


class DistributedEventStore(StoreBase):
    def __init__(self, js: JetStreamContext):
        super().__init__(js, prefix="events")

    async def store_event(self, run_id: str, event: ControlEvent):
        kv = await self._get_kv_store(run_id)
        event_type = event.__class__.__name__

        # Retrieve existing list of events for this type
        try:
            entry = await kv.get(event_type)
            event_list_data = json.loads(entry.value.decode())
        except Exception:
            event_list_data = []

        # Append new event data
        event_list_data.append(event.model_dump())
        # Remove duplicates based on 'event_id'
        event_list_data = list({event["event_id"]: event for event in event_list_data}.values())

        # Store updated list
        await kv.put(event_type, json.dumps(event_list_data).encode())

    async def get_events_of_type(self, run_id: str, event_type: Type[ControlEvent]) -> List[ControlEvent]:
        kv = await self._get_kv_store(run_id)
        try:
            entry = await kv.get(event_type.__name__)
            event_list_data = json.loads(entry.value.decode())
            return [event_type(**data) for data in event_list_data]
        except Exception:
            return []

    async def get_all_events(self, run_id: str, before: Optional[int] = None) -> Dict[str, List[ControlEvent]]:
        kv = await self._get_kv_store(run_id)
        events = {}
        keys = await kv.keys()
        for key in keys:
            event_class = ControlEvent._event_registry.get(key)
            if event_class:
                event_list = await self.get_events_of_type(run_id, event_class)
                if before:
                    events[key] = [event for event in event_list if event.created_at <= before]
                else:
                    events[key] = event_list
        return events
