import json
import logging
from typing import Optional

from flatdict import FlatterDict


from opentelemetry import trace

from lib_core.nats.events import DisplayEvent, ChunkEvent, ThoughtEvent
from lib_core.nats.publishers.JSPublisher import JSPublisher
from lib_core.nats.topic_managers.agents.AgentThreadTopicManager import AgentThreadTopicManager

logger = logging.getLogger(__name__)


class EventDisplayer:

    def __init__(self, publisher: JSPublisher, topic_manager: AgentThreadTopicManager):
        self.publisher = publisher
        self.topic_manager = topic_manager

    async def display_event(self, event: DisplayEvent, content: Optional[str] = None):
        subject = self.topic_manager.get_subject_for_display_event_in_thread(event.__class__.__name__, event.event_id)
        attributes = FlatterDict(event.model_dump(), delimiter=".").as_dict()

        current_span = trace.get_current_span()
        current_span.add_event(
            name=f"{event.__class__.__name__}: {content or json.dumps(attributes)}",
            attributes=attributes
        )

        await self.publisher.publish_event(event, subject)

    async def display_chunk(self, content: str):
        event = ChunkEvent(content=content)
        await self.display_event(event, content=content)

    async def display_thought(self, thought: str):
        event = ThoughtEvent(content=thought)
        await self.display_event(event, content=thought)
