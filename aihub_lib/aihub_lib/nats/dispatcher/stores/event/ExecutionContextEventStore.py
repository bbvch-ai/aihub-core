from collections import defaultdict
from dataclasses import dataclass
from typing import DefaultDict, Dict, List, Optional

from aihub_lib.nats.events import BaseEvent


@dataclass
class ExecutionContextEventStore:
    """Store for all events within a single run"""

    # Maps event_name -> event_id -> event
    events: DefaultDict[str, Dict[str, BaseEvent]] = None

    def __post_init__(self):
        if self.events is None:
            self.events = defaultdict(dict)

    def add_event(self, event: BaseEvent) -> None:
        """Add an event to the store"""
        event_name = event.event_name
        event_id = event.event_id
        self.events[event_name][event_id] = event

    def get_events_of_name(self, event_name: str, until_event: Optional[BaseEvent] = None) -> List[BaseEvent]:
        """Get all events of a specific type, optionally filtered by timestamp"""
        events = list(self.events.get(event_name, {}).values())

        if until_event is not None:
            events = [e for e in events if e.sequence_number <= until_event.sequence_number]

        # Sort by creation time for consistent ordering
        events.sort(key=lambda x: x.created_at)
        return events

    def get_events_of_multiple_names(
        self, event_names: List[str], until_event: Optional[BaseEvent] = None
    ) -> Dict[str, List[BaseEvent]]:
        """Get events of multiple types, organized by type name"""
        result = {}
        for event_name in event_names:
            result[event_name] = self.get_events_of_name(event_name, until_event)
        return result
