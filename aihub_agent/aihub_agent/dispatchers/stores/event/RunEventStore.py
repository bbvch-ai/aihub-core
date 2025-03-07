from collections import defaultdict
from dataclasses import dataclass
from typing import DefaultDict, Dict, List, Optional

from aihub_lib.nats.events import ControlEvent


@dataclass
class RunEventStore:
    """Store for all events within a single run"""

    # Maps event_type -> event_id -> event
    events: DefaultDict[str, Dict[str, ControlEvent]] = None

    def __post_init__(self):
        if self.events is None:
            self.events = defaultdict(dict)

    def add_event(self, event: ControlEvent) -> None:
        """Add an event to the store"""
        event_type = event.__class__.__name__
        event_id = event.event_id
        self.events[event_type][event_id] = event

    def get_events_of_type(self, event_type: str, before: Optional[int] = None) -> List[ControlEvent]:
        """Get all events of a specific type, optionally filtered by timestamp"""
        events = list(self.events.get(event_type, {}).values())

        if before is not None:
            events = [e for e in events if e.created_at <= before]

        # Sort by creation time for consistent ordering
        events.sort(key=lambda x: x.created_at)
        return events

    def get_events_of_multiple_types(
        self, event_types: List[str], before: Optional[int] = None
    ) -> Dict[str, List[ControlEvent]]:
        """Get events of multiple types, organized by type name"""
        result = {}
        for event_type in event_types:
            result[event_type] = self.get_events_of_type(event_type, before)
        return result
